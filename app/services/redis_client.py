import redis.asyncio as aioredis

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_client: aioredis.Redis | None = None


async def init_redis(url: str) -> None:
    global _client
    _client = aioredis.from_url(url, decode_responses=True)
    await _client.ping()
    logger.info("Redis connection established: %s", url)


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis connection closed.")


def get_redis_client() -> aioredis.Redis | None:
    return _client
