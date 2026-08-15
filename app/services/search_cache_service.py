import json

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.database.repositories import get_cached_search, save_search_cache
from app.services.deezer_service import search_tracks
from app.services.redis_client import get_redis_client
from app.utils.logger import setup_logger
from app.utils.metrics import search_cache_hits_total, search_cache_misses_total
from app.utils.types import TrackDict

logger = setup_logger(__name__)

SEARCH_CACHE_SOURCE = "deezer"
SEARCH_CACHE_TTL_SECONDS = 24 * 60 * 60


def normalize_query(query: str) -> str:
    """Normalizes a search query for cache-key matching (lowercase + trim)."""
    return query.strip().lower()


def _redis_key(normalized: str) -> str:
    return f"searchcache:{SEARCH_CACHE_SOURCE}:{normalized}"


async def _redis_get(client: aioredis.Redis, normalized: str) -> list[TrackDict] | None:
    """
    Reads cached results from Redis. Redis expires the key itself via SETEX,
    so a present key is by definition still within the 24h window.
    """
    raw = await client.get(_redis_key(normalized))

    if not raw:
        return None

    try:
        tracks = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("Discarding unreadable Redis search cache for %r", normalized)
        return None

    if not isinstance(tracks, list):
        return None

    return tracks


async def _redis_set(client: aioredis.Redis, normalized: str, tracks: list[TrackDict]) -> None:
    await client.setex(
        _redis_key(normalized),
        SEARCH_CACHE_TTL_SECONDS,
        json.dumps(tracks),
    )


async def search_tracks_cached(query: str, limit: int) -> list[TrackDict]:
    """
    Returns Deezer search results from a 24h cache keyed on the normalized
    query + source. Calls the Deezer API only on a full cache miss.

    Two cache tiers, both 24h:

    - Redis (fast path) — checked first, written on every fill.
    - PostgreSQL (durable) — the source of truth. Still read on a Redis miss
      and still written on every fill, so a Redis restart, eviction, or outage
      costs latency but never a cold cache. This is why the PostgreSQL tier was
      kept rather than replaced.
    """
    normalized = normalize_query(query)
    client = get_redis_client()

    if client is not None:
        try:
            cached = await _redis_get(client, normalized)
            if cached is not None:
                logger.info("Search cache hit (redis) for %r", normalized)
                search_cache_hits_total.inc()
                return cached
        except RedisError as error:
            logger.warning("Redis unavailable for search cache, using PostgreSQL: %s", error)
            client = None

    cached = await get_cached_search(normalized, SEARCH_CACHE_SOURCE)
    if cached is not None:
        logger.info("Search cache hit (postgres) for %r", normalized)
        search_cache_hits_total.inc()

        # Warm Redis so the next lookup takes the fast path.
        if client is not None:
            try:
                await _redis_set(client, normalized, cached)
            except RedisError as error:
                logger.warning("Could not warm Redis search cache: %s", error)

        return cached

    logger.info("Search cache miss for %r — calling Deezer", normalized)
    search_cache_misses_total.inc()
    tracks = await search_tracks(query=query, limit=limit)

    if tracks:
        await save_search_cache(normalized, SEARCH_CACHE_SOURCE, tracks)

        if client is not None:
            try:
                await _redis_set(client, normalized, tracks)
            except RedisError as error:
                logger.warning("Could not write Redis search cache: %s", error)

    return tracks
