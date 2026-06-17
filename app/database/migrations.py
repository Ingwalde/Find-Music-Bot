"""
Lightweight incremental migrations for PostgreSQL.

On every startup, migrate_db() is called from init_db_pool() after create_tables_pg().
For a fresh database create_tables_pg() already includes all current columns, so
migrate_db() finds nothing missing and exits immediately (no-op).
For an older live database that predates a column addition, migrate_db() adds the
missing column via ALTER TABLE, making the startup path self-healing without manual DDL.

All table_name / column_name values passed to add_column_if_missing are internal
constants defined below — no user input reaches the f-string in that function.
"""


async def get_table_columns(conn, table_name: str) -> set[str]:
    """
    Returns the set of column names present in table_name (public schema).
    Uses information_schema — the standard PostgreSQL introspection view.
    """
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = $1",
        table_name,
    )
    return {r["column_name"] for r in rows}


async def add_column_if_missing(
    conn,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    """
    Adds column_name to table_name if it is not already present.
    table_name and column_name are always hardcoded internal constants (see migrate_db).
    """
    columns = await get_table_columns(conn, table_name)
    if column_name not in columns:
        await conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"  # noqa: S608
        )


async def migrate_db(conn) -> None:
    """
    Applies incremental column migrations for PostgreSQL.
    Idempotent — safe to run on every startup.
    Uses TIMESTAMPTZ to match the column types in create_tables_pg.
    """
    await add_column_if_missing(conn, "users", "language", "TEXT DEFAULT 'en'")
    await add_column_if_missing(conn, "users", "last_track_id", "TEXT")

    await add_column_if_missing(conn, "tracks", "release_date", "TEXT")
    await add_column_if_missing(conn, "tracks", "rank", "INTEGER")
    await add_column_if_missing(conn, "tracks", "popularity", "TEXT")
    await add_column_if_missing(conn, "tracks", "updated_at", "TIMESTAMPTZ")
    await add_column_if_missing(conn, "tracks", "spotify_track_id", "TEXT")
    await add_column_if_missing(conn, "tracks", "spotify_link", "TEXT")
    await add_column_if_missing(conn, "tracks", "spotify_updated_at", "TIMESTAMPTZ")
