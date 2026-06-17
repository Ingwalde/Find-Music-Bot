import pytest

from app.database.migrations import add_column_if_missing, get_table_columns, migrate_db


@pytest.mark.asyncio
async def test_get_table_columns_returns_real_columns(live_pg):
    async with live_pg.acquire() as conn:
        cols = await get_table_columns(conn, "users")

    assert "id" in cols
    assert "telegram_id" in cols
    assert "language" in cols
    assert "last_track_id" in cols
    assert "created_at" in cols


@pytest.mark.asyncio
async def test_add_column_if_missing_adds_absent_column(live_pg):
    async with live_pg.acquire() as conn:
        # Drop the column so it is genuinely absent.
        await conn.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_track_id")
        cols_before = await get_table_columns(conn, "users")
        assert "last_track_id" not in cols_before

        # add_column_if_missing should detect the gap and add it.
        await add_column_if_missing(conn, "users", "last_track_id", "TEXT")
        cols_after = await get_table_columns(conn, "users")

    assert "last_track_id" in cols_after


@pytest.mark.asyncio
async def test_add_column_if_missing_is_noop_when_column_exists(live_pg):
    async with live_pg.acquire() as conn:
        cols_before = await get_table_columns(conn, "users")
        assert "language" in cols_before

        # Calling again must not raise and must leave the column intact.
        await add_column_if_missing(conn, "users", "language", "TEXT DEFAULT 'en'")
        cols_after = await get_table_columns(conn, "users")

    assert "language" in cols_after


@pytest.mark.asyncio
async def test_migrate_db_is_idempotent(live_pg):
    async with live_pg.acquire() as conn:
        # Run twice — must not raise on either call.
        await migrate_db(conn)
        await migrate_db(conn)

        cols_users = await get_table_columns(conn, "users")
        cols_tracks = await get_table_columns(conn, "tracks")

    # users columns managed by migrate_db
    assert "language" in cols_users
    assert "last_track_id" in cols_users

    # tracks columns managed by migrate_db
    assert "release_date" in cols_tracks
    assert "rank" in cols_tracks
    assert "popularity" in cols_tracks
    assert "updated_at" in cols_tracks
    assert "spotify_track_id" in cols_tracks
    assert "spotify_link" in cols_tracks
    assert "spotify_updated_at" in cols_tracks
