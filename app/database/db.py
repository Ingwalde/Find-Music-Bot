import asyncio

import asyncpg

from app.config.settings import settings

# ── pool singleton ────────────────────────────────────────────────────────────

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Returns the active asyncpg pool.
    Raises RuntimeError if init_db_pool() has not been called.
    """
    if _pool is None:
        raise RuntimeError("Pool not initialized — call init_db_pool() first")
    return _pool


async def init_db_pool() -> None:
    """
    Creates the asyncpg connection pool.
    Idempotent — calling more than once is safe and has no effect.

    Schema setup (tables, indexes, column migrations) is owned by Alembic,
    not this function — run `alembic upgrade head` before the bot starts
    (see deploy/Dockerfile). This function assumes the schema already exists.
    """
    global _pool
    if _pool is None:
        _pool = await asyncio.wait_for(
            asyncpg.create_pool(settings.DATABASE_URL, min_size=2, max_size=10),
            timeout=10.0,
        )


async def close_db_pool() -> None:
    """
    Closes the asyncpg pool and resets the singleton.
    Safe to call when the pool has not been initialised.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


__all__ = [
    "get_pool",
    "init_db_pool",
    "close_db_pool",
]
