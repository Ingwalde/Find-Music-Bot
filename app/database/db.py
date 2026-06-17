import asyncpg

from app.config.settings import settings
from app.database.indexes import create_indexes_pg
from app.database.migrations import migrate_db
from app.database.schema import create_tables_pg
from app.version import __version__


async def record_schema_version_pg(conn, version: str = __version__) -> None:
    """
    Records the current schema version in PostgreSQL.
    Uses ON CONFLICT DO NOTHING — PostgreSQL equivalent of INSERT OR IGNORE.
    """
    await conn.execute(
        """
        INSERT INTO schema_migrations (version) VALUES ($1)
        ON CONFLICT (version) DO NOTHING
        """,
        version,
    )


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
    Creates the asyncpg connection pool and initialises the PostgreSQL schema.
    Idempotent — calling more than once is safe and has no effect.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL, min_size=2, max_size=10
        )
        async with _pool.acquire() as conn:
            await create_tables_pg(conn)
            await migrate_db(conn)
            await create_indexes_pg(conn)
            await record_schema_version_pg(conn)


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
    "record_schema_version_pg",
]
