"""
Integration tests for async PostgreSQL users.py repository.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.
"""

from types import SimpleNamespace

import pytest

import app.database.repository_modules.users as users_module
from app.localization.languages import DEFAULT_LANGUAGE

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_user(user_id: int = 111_222_333, username: str = "tester", first_name: str = "Test"):
    return SimpleNamespace(id=user_id, username=username, first_name=first_name)


# ── upsert_user ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_user_inserts_new_user(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    async with live_pg.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT telegram_id, username, first_name FROM users WHERE telegram_id = $1",
            user.id,
        )

    assert row is not None
    assert row["username"] == "tester"
    assert row["first_name"] == "Test"


@pytest.mark.asyncio
async def test_upsert_user_updates_username_and_first_name(live_pg):
    user = make_user(username="old_name", first_name="Old")
    await users_module.upsert_user(user)

    updated = make_user(username="new_name", first_name="New")
    await users_module.upsert_user(updated)

    async with live_pg.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT username, first_name FROM users WHERE telegram_id = $1",
            user.id,
        )

    assert row["username"] == "new_name"
    assert row["first_name"] == "New"


@pytest.mark.asyncio
async def test_upsert_user_preserves_language_on_conflict(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.set_user_language(user.id, "uk")

    await users_module.upsert_user(make_user(username="same_id_new_username"))

    language = await users_module.get_user_language(user.id)
    assert language == "uk"


# ── get_user_id ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_id_returns_int_after_insert(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    user_id = await users_module.get_user_id(user.id)

    assert user_id is not None
    assert isinstance(user_id, int)
    assert user_id > 0


@pytest.mark.asyncio
async def test_get_user_id_returns_none_for_unknown(live_pg):
    result = await users_module.get_user_id(telegram_id=99999)
    assert result is None


# ── get_user_language ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_language_returns_default_when_telegram_id_is_none(live_pg):
    result = await users_module.get_user_language(telegram_id=None)
    assert result == DEFAULT_LANGUAGE


@pytest.mark.asyncio
async def test_get_user_language_returns_default_for_unknown_user(live_pg):
    result = await users_module.get_user_language(telegram_id=99999)
    assert result == DEFAULT_LANGUAGE


@pytest.mark.asyncio
async def test_get_user_language_returns_stored_language(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.set_user_language(user.id, "uk")

    result = await users_module.get_user_language(user.id)
    assert result == "uk"


@pytest.mark.asyncio
async def test_get_user_language_falls_back_for_unsupported_value(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    async with live_pg.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language = $1 WHERE telegram_id = $2",
            "xx",
            user.id,
        )

    result = await users_module.get_user_language(user.id)
    assert result == DEFAULT_LANGUAGE


# ── set_user_language ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_user_language_stores_valid_language(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.set_user_language(user.id, "de")

    result = await users_module.get_user_language(user.id)
    assert result == "de"


@pytest.mark.asyncio
async def test_set_user_language_falls_back_for_unsupported_language(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.set_user_language(user.id, "zz")

    result = await users_module.get_user_language(user.id)
    assert result == DEFAULT_LANGUAGE


# ── save_last_track_id / get_last_track_id ────────────────────────────────────


@pytest.mark.asyncio
async def test_save_and_get_last_track_id(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.save_last_track_id(user.id, "99887766")

    result = await users_module.get_last_track_id(user.id)
    assert result == "99887766"


@pytest.mark.asyncio
async def test_get_last_track_id_returns_none_before_any_save(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    result = await users_module.get_last_track_id(user.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_last_track_id_returns_none_for_unknown_user(live_pg):
    result = await users_module.get_last_track_id(telegram_id=99999)
    assert result is None


@pytest.mark.asyncio
async def test_save_last_track_id_overwrites_previous_value(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await users_module.save_last_track_id(user.id, "111")
    await users_module.save_last_track_id(user.id, "222")

    result = await users_module.get_last_track_id(user.id)
    assert result == "222"
