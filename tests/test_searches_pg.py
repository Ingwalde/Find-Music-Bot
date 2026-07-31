"""
Integration tests for async PostgreSQL searches.py repository.
Uses the compose "test-postgres" service via the shared live_pg fixture from conftest.py.

searches.py has FK dependency on users (get_user_id), so each test
creates a user first via users_module.
"""

from types import SimpleNamespace

import pytest

import app.database.repository_modules.searches as searches_module
import app.database.repository_modules.users as users_module


def make_user(user_id: int = 555_666_777, username: str = "searcher", first_name: str = "Searcher"):
    return SimpleNamespace(id=user_id, username=username, first_name=first_name)


# ── save_search ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_search_inserts_query(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "ABBA SOS")

    history = await searches_module.get_search_history(user.id)
    assert len(history) == 1
    assert history[0]["query"] == "ABBA SOS"


@pytest.mark.asyncio
async def test_save_search_ignores_blank_query(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "   ")

    history = await searches_module.get_search_history(user.id)
    assert history == []


@pytest.mark.asyncio
async def test_save_search_ignores_unknown_user(live_pg):
    await searches_module.save_search(99999, "anything")

    history = await searches_module.get_search_history(99999)
    assert history == []


# ── get_search_history ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_search_history_respects_limit(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    for i in range(5):
        await searches_module.save_search(user.id, f"query {i}")

    history = await searches_module.get_search_history(user.id, limit=3)
    assert len(history) == 3


@pytest.mark.asyncio
async def test_get_search_history_dedupes_by_normalized_query(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "American Pie")
    await searches_module.save_search(user.id, "music")
    await searches_module.save_search(user.id, "american pie")  # duplicate, different case

    history = await searches_module.get_search_history(user.id, limit=10)
    queries = [item["query"] for item in history]

    assert len(queries) == 2
    assert queries[0] == "american pie"  # latest replaces original, sorted newest-first
    assert "music" in queries


@pytest.mark.asyncio
async def test_get_search_history_returns_empty_for_unknown_user(live_pg):
    result = await searches_module.get_search_history(99999)
    assert result == []


# ── trim_search_history (exercised via save_search) ──────────────────────────


@pytest.mark.asyncio
async def test_save_search_trims_old_entries_beyond_max(live_pg, monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "MAX_HISTORY_PER_USER", 3)

    user = make_user()
    await users_module.upsert_user(user)
    for i in range(6):
        await searches_module.save_search(user.id, f"unique query {i}")

    user_id = await users_module.get_user_id(user.id)
    async with live_pg.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM searches WHERE user_id = $1",
            user_id,
        )
    assert count == 3


# ── get_search_query_by_id ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_search_query_by_id_returns_correct_query(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "ABBA SOS")

    history = await searches_module.get_search_history(user.id, limit=1)
    search_id = history[0]["id"]

    result = await searches_module.get_search_query_by_id(user.id, search_id)
    assert result == "ABBA SOS"


@pytest.mark.asyncio
async def test_get_search_query_by_id_returns_none_for_wrong_owner(live_pg):
    user1 = make_user(user_id=100)
    user2 = make_user(user_id=200, username="other")
    await users_module.upsert_user(user1)
    await users_module.upsert_user(user2)
    await searches_module.save_search(user1.id, "ABBA SOS")

    history = await searches_module.get_search_history(user1.id, limit=1)
    search_id = history[0]["id"]

    result = await searches_module.get_search_query_by_id(user2.id, search_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_search_query_by_id_returns_none_for_missing_id(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    result = await searches_module.get_search_query_by_id(user.id, 999999)
    assert result is None


# ── clear_search_history ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_search_history_empties_table(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "query 1")
    await searches_module.save_search(user.id, "query 2")

    await searches_module.clear_search_history(user.id)

    history = await searches_module.get_search_history(user.id)
    assert history == []


@pytest.mark.asyncio
async def test_clear_search_history_ignores_unknown_user(live_pg):
    await searches_module.clear_search_history(99999)

    result = await searches_module.get_search_history(99999)
    assert result == []
