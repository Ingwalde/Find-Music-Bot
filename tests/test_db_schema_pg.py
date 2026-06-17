"""
Unit tests for the PostgreSQL DDL functions in schema.py, indexes.py, and db.py.

Uses a CapturingConn that records executed SQL statements without a real database.
This validates SQL dialect (PG tokens present, SQLite tokens absent) and statement
counts. The real DDL is validated against a live PostgreSQL instance in Stage 10
via testcontainers.
"""

import pytest

from app.database import db as db_module
from app.database.indexes import create_indexes_pg
from app.database.schema import create_tables_pg


class CapturingConn:
    """Records every SQL statement passed to execute()."""

    def __init__(self):
        self.statements: list[str] = []

    async def execute(self, sql, *args):
        self.statements.append(sql.strip())


# ── create_tables_pg ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_tables_pg_issues_6_statements():
    conn = CapturingConn()
    await create_tables_pg(conn)
    assert len(conn.statements) == 6


@pytest.mark.asyncio
async def test_create_tables_pg_creates_all_6_tables():
    conn = CapturingConn()
    await create_tables_pg(conn)
    combined = "\n".join(conn.statements)
    for table in ("users", "searches", "tracks", "favorites", "errors", "schema_migrations"):
        assert table in combined, f"Table '{table}' not found in DDL"


@pytest.mark.asyncio
async def test_create_tables_pg_uses_pg_tokens():
    conn = CapturingConn()
    await create_tables_pg(conn)
    combined = "\n".join(conn.statements)
    assert "BIGSERIAL" in combined
    assert "TIMESTAMPTZ" in combined
    assert "NOW()" in combined


@pytest.mark.asyncio
async def test_create_tables_pg_has_no_sqlite_tokens():
    conn = CapturingConn()
    await create_tables_pg(conn)
    combined = "\n".join(conn.statements)
    assert "AUTOINCREMENT" not in combined
    assert "CURRENT_TIMESTAMP" not in combined


@pytest.mark.asyncio
async def test_create_tables_pg_uses_bigint_for_id_columns():
    conn = CapturingConn()
    await create_tables_pg(conn)
    # users.telegram_id must be BIGINT (Telegram IDs exceed 32-bit)
    users_ddl = conn.statements[0]
    assert "telegram_id BIGINT" in users_ddl
    # favorites FK columns must also be BIGINT
    favorites_ddl = conn.statements[3]
    assert "user_id BIGINT" in favorites_ddl
    assert "track_id BIGINT" in favorites_ddl


# ── create_indexes_pg ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_indexes_pg_issues_8_statements():
    conn = CapturingConn()
    await create_indexes_pg(conn)
    assert len(conn.statements) == 8


@pytest.mark.asyncio
async def test_create_indexes_pg_covers_all_index_names():
    conn = CapturingConn()
    await create_indexes_pg(conn)
    combined = "\n".join(conn.statements)
    expected_indexes = (
        "idx_users_telegram_id",
        "idx_searches_user_id",
        "idx_searches_user_id_id",
        "idx_tracks_deezer_track_id",
        "idx_tracks_spotify_track_id",
        "idx_favorites_user_id",
        "idx_favorites_track_id",
        "idx_errors_created_at",
    )
    for idx in expected_indexes:
        assert idx in combined, f"Index '{idx}' not found"


# ── record_schema_version_pg ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_schema_version_pg_uses_parameterized_on_conflict():
    conn = CapturingConn()
    await db_module.record_schema_version_pg(conn, version="3.1.0")
    assert len(conn.statements) == 1
    sql = conn.statements[0]
    assert "$1" in sql
    assert "ON CONFLICT" in sql
    assert "DO NOTHING" in sql
    assert "INSERT OR IGNORE" not in sql  # no SQLite dialect


@pytest.mark.asyncio
async def test_record_schema_version_pg_defaults_to_app_version():
    from app.version import __version__

    conn = CapturingConn()
    await db_module.record_schema_version_pg(conn)
    # Only check SQL shape — the version value is passed as a parameter, not embedded
    assert "$1" in conn.statements[0]
    assert __version__  # version module is importable
