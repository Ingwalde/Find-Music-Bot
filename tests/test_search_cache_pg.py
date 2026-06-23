"""
Integration tests for async PostgreSQL search_cache.py repository.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.

Also proves the v3.1.2 Alembic revision (63ab83bf2873, add search_cache table)
applies cleanly through the same alembic upgrade head chain live_pg already
runs — no fixture changes were needed to pick up a new revision.
"""

import pytest

import app.database.repository_modules.search_cache as search_cache_module


def make_results():
    return [
        {"deezer_track_id": "1", "title": "SOS", "artist": "ABBA"},
        {"deezer_track_id": "2", "title": "Waterloo", "artist": "ABBA"},
    ]


@pytest.mark.asyncio
async def test_get_cached_search_returns_none_when_absent(live_pg):
    result = await search_cache_module.get_cached_search("abba", "deezer")
    assert result is None


@pytest.mark.asyncio
async def test_save_then_get_returns_cached_results(live_pg):
    results = make_results()
    await search_cache_module.save_search_cache("abba", "deezer", results)

    cached = await search_cache_module.get_cached_search("abba", "deezer")

    assert cached == results


@pytest.mark.asyncio
async def test_get_cached_search_is_scoped_by_source(live_pg):
    await search_cache_module.save_search_cache("abba", "deezer", make_results())

    assert await search_cache_module.get_cached_search("abba", "spotify") is None


@pytest.mark.asyncio
async def test_save_search_cache_overwrites_existing_entry(live_pg):
    await search_cache_module.save_search_cache("abba", "deezer", [{"title": "old"}])
    await search_cache_module.save_search_cache("abba", "deezer", [{"title": "new"}])

    cached = await search_cache_module.get_cached_search("abba", "deezer")

    assert cached == [{"title": "new"}]

    async with live_pg.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM search_cache WHERE query_normalized = $1 AND source = $2",
            "abba",
            "deezer",
        )
    assert count == 1


@pytest.mark.asyncio
async def test_stale_entry_is_ignored(live_pg):
    results = make_results()
    await search_cache_module.save_search_cache("abba", "deezer", results)

    async with live_pg.acquire() as conn:
        await conn.execute(
            """
            UPDATE search_cache
            SET created_at = NOW() - INTERVAL '25 hours'
            WHERE query_normalized = $1 AND source = $2
            """,
            "abba",
            "deezer",
        )

    cached = await search_cache_module.get_cached_search("abba", "deezer")

    assert cached is None


@pytest.mark.asyncio
async def test_entry_just_under_24_hours_is_still_fresh(live_pg):
    results = make_results()
    await search_cache_module.save_search_cache("abba", "deezer", results)

    async with live_pg.acquire() as conn:
        await conn.execute(
            """
            UPDATE search_cache
            SET created_at = NOW() - INTERVAL '23 hours'
            WHERE query_normalized = $1 AND source = $2
            """,
            "abba",
            "deezer",
        )

    cached = await search_cache_module.get_cached_search("abba", "deezer")

    assert cached == results
