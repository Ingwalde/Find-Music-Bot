from urllib.parse import urlsplit

import redis.asyncio as aioredis

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_client: aioredis.Redis | None = None


def _safe_target(url: str) -> str:
    """
    Returns host:port from a Redis URL, dropping any credentials.

    Redis passwords travel in the URL itself (redis://:secret@host:6379), so
    logging the URL verbatim writes the password to stdout and to the log file
    on every startup. The current deployment has no password, so nothing has
    leaked — this is here before a managed Redis introduces one.
    """
    try:
        parts = urlsplit(url)
        if parts.hostname:
            return f"{parts.hostname}:{parts.port}" if parts.port else parts.hostname
    except ValueError:
        pass

    return "<unparseable url>"


async def init_redis(url: str) -> None:
    global _client
    _client = aioredis.from_url(url, decode_responses=True)
    await _client.ping()
    logger.info("Redis connection established: %s", _safe_target(url))


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis connection closed.")


def get_redis_client() -> aioredis.Redis | None:
    return _client
