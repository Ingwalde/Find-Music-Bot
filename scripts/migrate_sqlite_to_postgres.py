"""
One-time migration script: SQLite → PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_postgres.py [--force]

Requirements:
    DATABASE_PATH — path to the SQLite file (read-only; never modified).
    DATABASE_URL  — PostgreSQL connection string.

Safety:
    - Aborts if any target PG table already contains rows (use --force to override).
    - SQLite file is opened read-only and never written to.
    - Explicit IDs are preserved so FK references remain valid.
    - BIGSERIAL sequences are reset after bulk insert to avoid collision.
    - Row counts are verified after migration; exits non-zero on mismatch.
"""

import argparse
import asyncio
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

# Allow running from the project root without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncpg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.config.settings import settings  # noqa: E402

# Timestamp columns per table — explicit for precise type conversion.
# SQLite stores TIMESTAMPTZ values as plain strings; asyncpg requires datetime objects.
_TIMESTAMP_COLS: dict[str, frozenset[str]] = {
    "schema_migrations": frozenset({"applied_at"}),
    "users":             frozenset({"created_at"}),
    "tracks":            frozenset({"created_at", "updated_at", "spotify_updated_at"}),
    "searches":          frozenset({"created_at"}),
    "favorites":         frozenset({"created_at"}),
    "errors":            frozenset({"created_at"}),
}


def _parse_ts(value: str | None) -> datetime | None:
    """Converts a SQLite timestamp string to a UTC-aware datetime, or passes None through."""
    if value is None:
        return None
    # fromisoformat handles 'YYYY-MM-DD HH:MM:SS' (SQLite CURRENT_TIMESTAMP format).
    # .replace(tzinfo=timezone.utc) preserves the original UTC instant in TIMESTAMPTZ.
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def _convert_row(table: str, cols: list[str], row: tuple) -> tuple:
    """Converts timestamp string columns to timezone-aware datetimes before PG insert."""
    ts_cols = _TIMESTAMP_COLS.get(table, frozenset())
    if not ts_cols:
        return row
    return tuple(_parse_ts(v) if col in ts_cols else v for col, v in zip(cols, row, strict=True))


# FK-safe migration order: referenced tables before referencing tables.
TABLES = [
    "schema_migrations",
    "users",
    "tracks",
    "searches",
    "favorites",
    "errors",
]

# Tables that have a BIGSERIAL primary key that needs a sequence reset.
TABLES_WITH_SERIAL = [
    "schema_migrations",
    "users",
    "tracks",
    "searches",
    "favorites",
    "errors",
]


def _sqlite_rows(sqlite_path: str, table: str) -> tuple[list[str], list[tuple]]:
    """Returns (column_names, rows) from the SQLite table."""
    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")  # noqa: S608
        rows = cur.fetchall()
        if not rows:
            return [], []
        cols = list(rows[0].keys())
        return cols, [tuple(r) for r in rows]
    finally:
        conn.close()


def _sqlite_count(sqlite_path: str, table: str) -> int:
    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
        return cur.fetchone()[0]
    finally:
        conn.close()


async def _pg_count(conn, table: str) -> int:
    return await conn.fetchval(f"SELECT COUNT(*) FROM {table}")  # noqa: S608


async def _pg_any_rows(conn) -> bool:
    """Returns True if ANY of the migration target tables contain rows."""
    for table in TABLES:
        count = await _pg_count(conn, table)
        if count > 0:
            return True
    return False


async def _reset_sequence(conn, table: str) -> None:
    """Resets the BIGSERIAL sequence to MAX(id) so future inserts don't collide."""
    await conn.execute(
        f"""
        SELECT setval(
            pg_get_serial_sequence('{table}', 'id'),
            COALESCE((SELECT MAX(id) FROM {table}), 1)
        )
        """  # noqa: S608
    )


async def migrate(sqlite_path: str, database_url: str, force: bool) -> None:
    print(f"Source (SQLite): {sqlite_path}")
    print(f"Target (PG):     {database_url}\n")

    conn = await asyncpg.connect(database_url)
    try:
        # Safety check: abort if target is non-empty.
        if await _pg_any_rows(conn):
            if not force:
                print(
                    "ERROR: PostgreSQL target tables are not empty.\n"
                    "       Run with --force to migrate anyway (will INSERT duplicates).\n"
                    "       Aborting."
                )
                sys.exit(1)
            print("WARNING: --force passed; target tables are non-empty. Proceeding.\n")

        # Migrate each table.
        sqlite_counts: dict[str, int] = {}
        pg_counts_before: dict[str, int] = {}

        for table in TABLES:
            sqlite_n = _sqlite_count(sqlite_path, table)
            sqlite_counts[table] = sqlite_n
            pg_counts_before[table] = await _pg_count(conn, table)

            if sqlite_n == 0:
                print(f"  {table:<20} 0 rows — skipped")
                continue

            cols, rows = _sqlite_rows(sqlite_path, table)
            if not rows:
                print(f"  {table:<20} 0 rows — skipped")
                continue

            placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
            col_list = ", ".join(cols)
            sql = (
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "  # noqa: S608
                f"ON CONFLICT DO NOTHING"
            )

            converted = [_convert_row(table, cols, row) for row in rows]
            await conn.executemany(sql, converted)
            print(f"  {table:<20} {sqlite_n} row(s) inserted")

        # Reset BIGSERIAL sequences for all tables that have an id column.
        print("\nResetting sequences...")
        for table in TABLES_WITH_SERIAL:
            await _reset_sequence(conn, table)
            print(f"  {table:<20} sequence reset")

        # Verify row counts.
        print("\nVerifying row counts...")
        all_ok = True
        print(f"  {'Table':<20} {'SQLite':>8}  {'PG':>8}  Status")
        print(f"  {'-'*20} {'-'*8}  {'-'*8}  ------")

        for table in TABLES:
            pg_n = await _pg_count(conn, table)
            expected = sqlite_counts[table]
            ok = pg_n >= expected  # >= to handle pre-existing rows when --force used
            status = "✅" if ok else "❌ MISMATCH"
            print(f"  {table:<20} {expected:>8}  {pg_n:>8}  {status}")
            if not ok:
                all_ok = False

        if not all_ok:
            print("\nERROR: Row count mismatch detected. Migration may be incomplete.")
            sys.exit(1)

        print("\n✅ Migration complete.")

    finally:
        await conn.close()


def _run_alembic_upgrade() -> None:
    """
    Runs alembic upgrade head to ensure the target schema exists before
    migrating data. Must run in a sync context, before asyncio.run(migrate(...))
    starts — alembic's async template calls asyncio.run() internally
    (via migrations/env.py), which cannot be nested inside an already-running
    event loop.
    """
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    command.upgrade(cfg, "head")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if target PostgreSQL tables are non-empty.",
    )
    args = parser.parse_args()

    sqlite_path = settings.DATABASE_PATH
    database_url = settings.DATABASE_URL

    if not sqlite_path:
        print("ERROR: DATABASE_PATH is not set.")
        sys.exit(1)

    if not Path(sqlite_path).exists():
        print(f"ERROR: SQLite file not found: {sqlite_path}")
        sys.exit(1)

    if not database_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    print("Creating PostgreSQL schema (alembic upgrade head)...")
    _run_alembic_upgrade()
    print("Schema ready.\n")

    asyncio.run(migrate(sqlite_path, database_url, force=args.force))


if __name__ == "__main__":
    main()
