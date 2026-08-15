from typing import Any

from app.config.settings import settings
from app.database.db import get_pool
from app.version import __version__

MAINTENANCE_TABLES = (
    "users",
    "searches",
    "tracks",
    "favorites",
    "errors",
    "search_cache",
    "schema_migrations",
)


async def get_maintenance_table_names() -> tuple[str, ...]:
    """
    Returns PostgreSQL tables visible in maintenance reports.

    Queries information_schema.tables so a table dropped from the schema
    doesn't linger here, but the result is intersected with MAINTENANCE_TABLES
    — that tuple is the actual allowlist ceiling for get_table_count, not just
    a DB-failure fallback, so a real-but-unlisted table (e.g. alembic_version)
    is never returned. Falls back to MAINTENANCE_TABLES outright on any DB
    failure.
    """
    try:
        async with (await get_pool()).acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
        existing = {str(row["table_name"]) for row in rows}
    except Exception:
        return MAINTENANCE_TABLES

    table_names = tuple(name for name in MAINTENANCE_TABLES if name in existing)

    return table_names or MAINTENANCE_TABLES


def format_bytes(size_bytes: int) -> str:
    """
    Formats byte values as a readable size string.
    """
    if size_bytes < 0:
        raise ValueError("size_bytes cannot be negative")

    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} GB"


async def get_database_size_bytes() -> int:
    """
    Returns PostgreSQL database size in bytes via pg_database_size.
    """
    async with (await get_pool()).acquire() as conn:
        return await conn.fetchval("SELECT pg_database_size(current_database())")


async def get_table_count(table_name: str) -> int:
    """
    Returns row count for a known table.

    The allowlist check runs against get_maintenance_table_names() (dynamic
    information_schema query) which falls back to the static MAINTENANCE_TABLES
    tuple on any DB failure. Either way the guard is in force — an unknown
    table_name raises ValueError before the f-string query executes.
    """
    if table_name not in await get_maintenance_table_names():
        raise ValueError(f"Unsupported table for maintenance stats: {table_name}")

    async with (await get_pool()).acquire() as conn:
        return int(await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}"))


async def get_table_counts() -> dict[str, int]:
    """
    Returns row counts for all maintenance-visible tables.

    One connection, one round-trip. Previously this awaited get_table_count()
    per table, each acquiring its own connection — 7 tables meant 8 acquires
    and 8 queries for a single /maintenance report.

    Table names come from get_maintenance_table_names(), which is intersected
    with the MAINTENANCE_TABLES allowlist, so interpolating them into the
    UNION is safe for the same reason get_table_count's f-string is.
    """
    table_names = await get_maintenance_table_names()

    if not table_names:
        return {}

    union = " UNION ALL ".join(
        f"SELECT '{name}' AS table_name, COUNT(*) AS row_count FROM {name}"
        for name in table_names
    )

    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(union)

    counts = {str(row["table_name"]): int(row["row_count"]) for row in rows}

    # Preserve the allowlist ordering rather than the DB's row order.
    return {name: counts.get(name, 0) for name in table_names}


async def get_schema_version() -> str:
    """
    Returns the current app version.

    Schema versioning is owned by Alembic (v3.1.1+) — schema_migrations is a
    legacy table nothing writes to anymore, so the running app version is the
    only value that's ever actually current.
    """
    return __version__


async def get_database_summary() -> dict[str, Any]:
    """
    Builds a database maintenance summary used by admin commands.

    "database_path" key is kept for admin_tools.format_maintenance_report
    compatibility — populated with current_database() (the PG db name) instead
    of a file path, which does not exist in PostgreSQL.
    """
    size_bytes = await get_database_size_bytes()

    async with (await get_pool()).acquire() as conn:
        db_name = await conn.fetchval("SELECT current_database()")

    return {
        "database_path": db_name,
        "database_size_bytes": size_bytes,
        "database_size": format_bytes(size_bytes),
        "table_counts": await get_table_counts(),
        "schema_version": await get_schema_version(),
        "app_version": __version__,
    }


async def cleanup_old_errors(keep_latest: int | None = None) -> dict[str, int]:
    """
    Keeps the newest error rows and removes older saved errors.
    """
    if keep_latest is None:
        keep_latest = settings.ERROR_HISTORY_LIMIT

    if keep_latest < 0:
        raise ValueError("keep_latest cannot be negative")

    before = await get_table_count("errors")

    async with (await get_pool()).acquire() as conn:
        if keep_latest == 0:
            await conn.execute("DELETE FROM errors")
        else:
            await conn.execute(
                """
                DELETE FROM errors
                WHERE id NOT IN (
                    SELECT id
                    FROM errors
                    ORDER BY id DESC
                    LIMIT $1
                )
                """,
                keep_latest,
            )

    after = await get_table_count("errors")

    return {"before": before, "after": after, "deleted": before - after}


async def cleanup_search_history(max_rows_per_user: int | None = None) -> dict[str, int]:
    """
    Keeps the newest search rows per user and removes older history entries.
    Uses a single connection for the per-user delete loop.
    """
    if max_rows_per_user is None:
        max_rows_per_user = settings.MAX_HISTORY_PER_USER

    if max_rows_per_user < 0:
        raise ValueError("max_rows_per_user cannot be negative")

    before = await get_table_count("searches")

    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        user_ids = [int(row["id"]) for row in rows]

        for user_id in user_ids:
            if max_rows_per_user == 0:
                await conn.execute(
                    "DELETE FROM searches WHERE user_id = $1",
                    user_id,
                )
            else:
                await conn.execute(
                    """
                    DELETE FROM searches
                    WHERE user_id = $1
                    AND id NOT IN (
                        SELECT id
                        FROM searches
                        WHERE user_id = $2
                        ORDER BY id DESC
                        LIMIT $3
                    )
                    """,
                    user_id,
                    user_id,
                    max_rows_per_user,
                )

    after = await get_table_count("searches")

    return {"before": before, "after": after, "deleted": before - after}


async def cleanup_expired_search_cache() -> dict[str, int]:
    """
    Deletes search_cache rows past the 24h freshness window.

    The cache is read with a lazy staleness check, so a stale row is never
    served — but nothing ever deleted it either. Every unique normalized query
    ever searched kept its full result_json blob forever. This is the active
    prune that was missing; the read path is unchanged.
    """
    before = await get_table_count("search_cache")

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            "DELETE FROM search_cache WHERE created_at < NOW() - INTERVAL '24 hours'"
        )

    after = await get_table_count("search_cache")

    return {"before": before, "after": after, "deleted": before - after}
