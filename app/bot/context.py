import asyncio
import json
from math import ceil
from time import time

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.services.redis_client import get_redis_client
from app.utils.logger import setup_logger
from app.utils.types import TrackDict

logger = setup_logger(__name__)

SEARCH_CONTEXT_TTL_SECONDS = 60 * 60

search_contexts: dict[int, dict] = {}
_search_context_lock = asyncio.Lock()


def _redis_key(user_id: int) -> str:
    return f"sc:{user_id}"


def _cleanup_expired_unlocked(current_time: float) -> int:
    """
    Removes expired in-memory search contexts. Assumes the lock is already held.
    """
    expired_user_ids = [
        user_id
        for user_id, context in search_contexts.items()
        if current_time - float(context.get("created_at", 0)) > SEARCH_CONTEXT_TTL_SECONDS
    ]

    for user_id in expired_user_ids:
        search_contexts.pop(user_id, None)

    return len(expired_user_ids)


def _get_context_unlocked(user_id: int) -> dict | None:
    """
    Returns user's last search context, or None if missing/expired.
    Expired contexts are removed lazily. Assumes the lock is already held.
    """
    context = search_contexts.get(user_id)

    if not context:
        return None

    created_at = float(context.get("created_at", 0))

    if time() - created_at > SEARCH_CONTEXT_TTL_SECONDS:
        search_contexts.pop(user_id, None)
        return None

    return context


def _total_pages(context: dict | None, page_size: int) -> int:
    """
    Returns total number of pages for the given context. Pure function, no lock needed.
    """
    if not context:
        return 0

    tracks = context.get("tracks", [])

    if not tracks:
        return 0

    return max(1, ceil(len(tracks) / page_size))


async def _redis_get(client: aioredis.Redis, user_id: int) -> dict | None:
    """
    Reads a context from Redis. Redis expires the key itself via SETEX, so no
    TTL check is needed here — a present key is by definition still fresh.
    """
    raw = await client.get(_redis_key(user_id))

    if not raw:
        return None

    try:
        context = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("Discarding unreadable search context for user %s.", user_id)
        return None

    if not isinstance(context, dict):
        return None

    return context


async def _redis_set(client: aioredis.Redis, user_id: int, context: dict) -> None:
    """
    Writes a context to Redis with the shared TTL.
    """
    await client.setex(
        _redis_key(user_id),
        SEARCH_CONTEXT_TTL_SECONDS,
        json.dumps(context),
    )


async def cleanup_expired_search_contexts(now: float | None = None) -> int:
    """
    Removes expired in-memory search contexts and returns the number of removed entries.

    Redis-backed contexts are expired by Redis itself and are not counted here.
    """
    current_time = time() if now is None else now

    async with _search_context_lock:
        return _cleanup_expired_unlocked(current_time)


async def save_search_context(user_id: int, query: str, tracks: list[TrackDict]) -> None:
    """
    Saves last search results for user.
    Used for pagination without calling Deezer API again.

    Stored in Redis when available so pagination survives a bot restart; falls
    back to the in-memory dict when Redis is down or not configured.
    """
    current_time = time()
    context = {
        "query": query,
        "tracks": tracks,
        "page": 0,
        "created_at": current_time,
    }

    client = get_redis_client()

    if client is not None:
        try:
            await _redis_set(client, user_id, context)
            return
        except RedisError as error:
            logger.warning("Redis unavailable for search context, using memory: %s", error)

    async with _search_context_lock:
        _cleanup_expired_unlocked(current_time)
        search_contexts[user_id] = context


async def get_search_context(user_id: int) -> dict | None:
    """
    Returns user's last search context.
    Expired contexts are removed lazily to avoid unbounded memory growth.
    """
    client = get_redis_client()

    if client is not None:
        try:
            return await _redis_get(client, user_id)
        except RedisError as error:
            logger.warning("Redis unavailable for search context, using memory: %s", error)

    async with _search_context_lock:
        return _get_context_unlocked(user_id)


async def get_total_pages(user_id: int, page_size: int) -> int:
    """
    Returns total number of pages for user's last search.
    """
    context = await get_search_context(user_id)
    return _total_pages(context, page_size)


async def set_search_page(user_id: int, page: int, page_size: int) -> int:
    """
    Sets current page safely and returns normalized page number.
    """
    client = get_redis_client()

    if client is not None:
        try:
            context = await _redis_get(client, user_id)

            if not context:
                return 0

            total_pages = _total_pages(context, page_size)
            normalized_page = 0 if total_pages <= 0 else max(0, min(page, total_pages - 1))
            context["page"] = normalized_page
            await _redis_set(client, user_id, context)
            return normalized_page
        except RedisError as error:
            logger.warning("Redis unavailable for search context, using memory: %s", error)

    async with _search_context_lock:
        context = _get_context_unlocked(user_id)

        if not context:
            return 0

        total_pages = _total_pages(context, page_size)

        if total_pages <= 0:
            context["page"] = 0
            return 0

        normalized_page = max(0, min(page, total_pages - 1))
        context["page"] = normalized_page
        return normalized_page


async def get_current_page(user_id: int) -> int:
    """
    Returns current page number for user's last search.
    """
    context = await get_search_context(user_id)

    if not context:
        return 0

    return int(context.get("page", 0))


async def get_page_tracks(user_id: int, page_size: int, page: int | None = None) -> list[TrackDict]:
    """
    Returns tracks for selected page.
    """
    context = await get_search_context(user_id)

    if not context:
        return []

    tracks = context.get("tracks", [])

    if page is None:
        page = int(context.get("page", 0))

    start = page * page_size
    end = start + page_size

    return tracks[start:end]
