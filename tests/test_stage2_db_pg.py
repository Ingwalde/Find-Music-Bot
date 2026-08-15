"""
Covers the v3.7.10 Stage 2 database changes against a real PostgreSQL.

Index shape and transaction behaviour cannot be checked with fakes — both are
properties of the database, so these are integration tests.
"""

import pytest

import app.database.maintenance as maintenance
import app.database.repository_modules.favorites as favorites_module
import app.database.repository_modules.tracks as tracks_module
import app.database.repository_modules.users as users_module


def make_track(track_id: str, artist: str = "ABBA", rank: int = 100) -> dict:
    return {
        "deezer_track_id": track_id,
        "title": f"Track {track_id}",
        "artist": artist,
        "album": "Album",
        "duration": "3:00",
        "duration_seconds": 180,
        "deezer_link": f"https://deezer.com/{track_id}",
        "rank": rank,
    }


# ── migration b7d92e4f1a03: index set ───────────────────────────────────────


@pytest.mark.asyncio
async def test_artist_rank_index_exists(live_pg):
    async with live_pg.acquire() as conn:
        rows = await conn.fetch(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'tracks'"
        )

    names = {r["indexname"] for r in rows}
    assert "idx_tracks_artist_rank" in names


@pytest.mark.asyncio
async def test_duplicate_indexes_are_gone_but_uniqueness_remains(live_pg):
    """
    The dropped indexes duplicated the UNIQUE constraint's own backing index.
    Dropping them must not weaken the constraint.
    """
    async with live_pg.acquire() as conn:
        rows = await conn.fetch(
            "SELECT indexname FROM pg_indexes WHERE tablename IN ('users', 'tracks')"
        )
        names = {r["indexname"] for r in rows}

        assert "idx_users_telegram_id" not in names
        assert "idx_tracks_deezer_track_id" not in names

        # The constraint indexes that made them redundant are still there.
        assert "users_telegram_id_key" in names
        assert "tracks_deezer_track_id_key" in names


@pytest.mark.asyncio
async def test_uniqueness_is_still_enforced_on_tracks(live_pg):
    """Proves the dropped index was redundant, not load-bearing."""
    await tracks_module.save_track(make_track("dup-1"))
    await tracks_module.save_track(make_track("dup-1", artist="Changed"))

    async with live_pg.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM tracks WHERE deezer_track_id = $1", "dup-1"
        )
        artist = await conn.fetchval(
            "SELECT artist FROM tracks WHERE deezer_track_id = $1", "dup-1"
        )

    assert count == 1
    assert artist == "Changed", "the UPSERT must still update in place"


@pytest.mark.asyncio
async def test_artist_lookup_uses_the_new_index(live_pg):
    """The index only earns its cost if the planner actually picks it."""
    for i in range(60):
        await tracks_module.save_track(make_track(f"idx-{i}", artist="Indexed", rank=i))

    async with live_pg.acquire() as conn:
        await conn.execute("ANALYZE tracks")
        plan = await conn.fetch(
            """
            EXPLAIN SELECT deezer_track_id FROM tracks
            WHERE artist = $1 AND deezer_track_id != $2
            ORDER BY rank DESC LIMIT 3
            """,
            "Indexed",
            "idx-0",
        )

    text = " ".join(r["QUERY PLAN"] for r in plan)
    assert "idx_tracks_artist_rank" in text, f"planner ignored the index:\n{text}"


# ── cleanup_search_history: atomicity and consistent counts ─────────────────


@pytest.mark.asyncio
async def test_cleanup_search_history_reports_consistent_counts(live_pg):
    await users_module.upsert_user(
        type("U", (), {"id": 9001, "username": "t", "first_name": "T"})()
    )
    user_id = await users_module.get_user_id(9001)

    async with live_pg.acquire() as conn:
        for i in range(10):
            await conn.execute(
                "INSERT INTO searches (user_id, query) VALUES ($1, $2)", user_id, f"q{i}"
            )

    result = await maintenance.cleanup_search_history(max_rows_per_user=3)

    assert result["before"] == 10
    assert result["after"] == 3
    assert result["deleted"] == result["before"] - result["after"]


@pytest.mark.asyncio
async def test_cleanup_search_history_rolls_back_on_failure(live_pg, monkeypatch):
    """
    The reason this one function needs a transaction: it issues one DELETE per
    user, so a failure partway used to leave the cleanup half applied.
    """
    await users_module.upsert_user(
        type("U", (), {"id": 9002, "username": "a", "first_name": "A"})()
    )
    await users_module.upsert_user(
        type("U", (), {"id": 9003, "username": "b", "first_name": "B"})()
    )

    async with live_pg.acquire() as conn:
        for telegram_id in (9002, 9003):
            uid = await conn.fetchval(
                "SELECT id FROM users WHERE telegram_id = $1", telegram_id
            )
            for i in range(5):
                await conn.execute(
                    "INSERT INTO searches (user_id, query) VALUES ($1, $2)", uid, f"q{i}"
                )
        total_before = await conn.fetchval("SELECT COUNT(*) FROM searches")

    calls = {"n": 0}

    class FailingConn:
        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        async def execute(self, *args, **kwargs):
            if args and "DELETE FROM searches" in str(args[0]):
                calls["n"] += 1
                if calls["n"] == 2:
                    raise RuntimeError("connection dropped mid-cleanup")
            return await self._inner.execute(*args, **kwargs)

    class WrappingPool:
        def __init__(self, pool):
            self._pool = pool

        def acquire(self):
            pool = self._pool

            class Ctx:
                async def __aenter__(self):
                    self._cm = pool.acquire()
                    return FailingConn(await self._cm.__aenter__())

                async def __aexit__(self, *exc):
                    return await self._cm.__aexit__(*exc)

            return Ctx()

    async def fake_get_pool():
        return WrappingPool(live_pg)

    monkeypatch.setattr(maintenance, "get_pool", fake_get_pool)

    with pytest.raises(RuntimeError):
        await maintenance.cleanup_search_history(max_rows_per_user=1)

    monkeypatch.undo()

    async with live_pg.acquire() as conn:
        total_after = await conn.fetchval("SELECT COUNT(*) FROM searches")

    assert total_after == total_before, (
        "the first user's deletes must roll back when the second fails"
    )


# ── add_favorite: no redundant UPSERT from the caller ───────────────────────


@pytest.mark.asyncio
async def test_add_favorite_stores_the_track_itself(live_pg):
    """
    favorites_callbacks used to call save_track() and then add_favorite(),
    which calls save_track() again — the same UPSERT twice per ⭐. Removing
    the caller's copy is only safe because add_favorite owns it.
    """
    await users_module.upsert_user(
        type("U", (), {"id": 9004, "username": "c", "first_name": "C"})()
    )

    await favorites_module.add_favorite(9004, make_track("solo-1"))

    async with live_pg.acquire() as conn:
        track_rows = await conn.fetchval(
            "SELECT COUNT(*) FROM tracks WHERE deezer_track_id = $1", "solo-1"
        )
        fav_rows = await conn.fetchval("SELECT COUNT(*) FROM favorites")

    assert track_rows == 1
    assert fav_rows == 1
