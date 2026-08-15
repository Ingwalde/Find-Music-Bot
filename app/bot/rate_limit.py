import asyncio
import uuid
from collections import deque
from time import time

import redis.asyncio as aioredis
from prometheus_client import Counter
from redis.exceptions import RedisError

from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_rate_limit_blocked = Counter(
    "bot_rate_limit_blocked_total",
    "Total number of requests blocked by rate limiting",
)

_request_timestamps: dict[int, deque] = {}
_warned_users: set[int] = set()
_rate_limit_lock = asyncio.Lock()

# Sweep idle entries only once the dict is big enough for the scan to be worth
# it — an O(n) pass on every request would cost more than the leak it prevents.
_EVICT_THRESHOLD = 1000


def _evict_idle_unlocked(current_time: float, window: float) -> None:
    """
    Drops users whose window has fully expired. Assumes the lock is held.

    Without this, _request_timestamps and _warned_users kept one entry per
    Telegram ID seen since process start, forever — the deque was drained of
    stale timestamps but the key itself was never removed. Only affects the
    in-memory fallback (Redis expires its own keys), so it leaked only while
    Redis was down or unconfigured, which is exactly when a restart is least
    welcome.
    """
    idle = [
        user_id
        for user_id, stamps in _request_timestamps.items()
        if not stamps or current_time - stamps[-1] > window
    ]

    for user_id in idle:
        del _request_timestamps[user_id]
        _warned_users.discard(user_id)


async def _check_rate_limit_memory(telegram_id: int) -> bool:
    current_time = time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS
    async with _rate_limit_lock:
        if len(_request_timestamps) > _EVICT_THRESHOLD:
            _evict_idle_unlocked(current_time, window)

        timestamps = _request_timestamps.setdefault(telegram_id, deque())
        while timestamps and current_time - timestamps[0] > window:
            timestamps.popleft()
        if len(timestamps) >= max_requests:
            _rate_limit_blocked.inc()
            return False
        timestamps.append(current_time)
        _warned_users.discard(telegram_id)
        return True


async def _check_rate_limit_redis(client: aioredis.Redis, telegram_id: int) -> bool:
    now = time()
    cutoff = now - settings.RATE_LIMIT_WINDOW_SECONDS
    key = f"rl:{telegram_id}"
    member = f"{now}:{uuid.uuid4().hex[:8]}"

    pipe = client.pipeline()
    pipe.zremrangebyscore(key, "-inf", cutoff)
    pipe.zadd(key, {member: now})
    pipe.zcard(key)
    pipe.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS * 2)
    results = await pipe.execute()

    count = results[2]
    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        await client.zrem(key, member)
        _rate_limit_blocked.inc()
        return False
    await client.delete(f"warn:{telegram_id}")
    return True


async def check_rate_limit(telegram_id: int, *, is_admin: bool = False) -> bool:
    if is_admin:
        return True

    from app.services.redis_client import get_redis_client

    client = get_redis_client()
    if client is not None:
        try:
            return await _check_rate_limit_redis(client, telegram_id)
        except (RedisError, OSError):
            logger.warning("Redis rate limit check failed, falling back to in-memory")

    return await _check_rate_limit_memory(telegram_id)


async def _should_warn_once_memory(telegram_id: int) -> bool:
    async with _rate_limit_lock:
        if telegram_id in _warned_users:
            return False
        _warned_users.add(telegram_id)
        return True


async def _should_warn_once_redis(client: aioredis.Redis, telegram_id: int) -> bool:
    key = f"warn:{telegram_id}"
    result = await client.set(key, "1", nx=True, ex=settings.RATE_LIMIT_WINDOW_SECONDS * 2)
    return result is not None


async def should_warn_once(telegram_id: int) -> bool:
    from app.services.redis_client import get_redis_client

    client = get_redis_client()
    if client is not None:
        try:
            return await _should_warn_once_redis(client, telegram_id)
        except (RedisError, OSError):
            logger.warning("Redis warn-once check failed, falling back to in-memory")

    return await _should_warn_once_memory(telegram_id)
