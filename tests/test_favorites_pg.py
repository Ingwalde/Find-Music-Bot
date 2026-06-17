"""
Integration tests for async PostgreSQL favorites.py repository.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.
"""

from types import SimpleNamespace

import pytest

import app.database.repository_modules.favorites as favorites_module
import app.database.repository_modules.tracks as tracks_module
import app.database.repository_modules.users as users_module


def make_user(user_id: int = 777_888_999, username: str = "fav_user", first_name: str = "Fav"):
    return SimpleNamespace(id=user_id, username=username, first_name=first_name)


def make_track(deezer_track_id="fav_track_001", title="Fav Song", artist="Fav Artist", rank=500):
    return {
        "deezer_track_id": deezer_track_id,
        "title": title,
        "artist": artist,
        "album": "Fav Album",
        "duration": "03:30",
        "duration_seconds": 210,
        "deezer_link": f"https://www.deezer.com/track/{deezer_track_id}",
        "cover_url": "https://e-cdns-images.dzcdn.net/images/cover/fav.jpg",
        "release_date": "2020-01-01",
        "rank": rank,
        "popularity": "High",
    }


# ── add_favorite / is_track_favorite ────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_favorite_links_user_and_track(live_pg):
    user = make_user()
    track = make_track()
    await users_module.upsert_user(user)
    await tracks_module.save_track(track)

    await favorites_module.add_favorite(user.id, track)

    user_id = await users_module.get_user_id(user.id)
    async with live_pg.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM favorites WHERE user_id = $1",
            user_id,
        )
    assert row is not None


@pytest.mark.asyncio
async def test_is_track_favorite_returns_true_after_add(live_pg):
    user = make_user()
    track = make_track()
    await users_module.upsert_user(user)
    await favorites_module.add_favorite(user.id, track)

    result = await favorites_module.is_track_favorite(user.id, track["deezer_track_id"])
    assert result is True


@pytest.mark.asyncio
async def test_is_track_favorite_returns_false_for_unknown_user(live_pg):
    result = await favorites_module.is_track_favorite(99999, "any_track")
    assert result is False


@pytest.mark.asyncio
async def test_add_favorite_on_conflict_do_nothing(live_pg):
    user = make_user()
    track = make_track()
    await users_module.upsert_user(user)

    await favorites_module.add_favorite(user.id, track)
    await favorites_module.add_favorite(user.id, track)

    user_id = await users_module.get_user_id(user.id)
    async with live_pg.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM favorites WHERE user_id = $1",
            user_id,
        )
    assert count == 1


# ── remove_favorite ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remove_favorite_removes_it(live_pg):
    user = make_user()
    track = make_track()
    await users_module.upsert_user(user)
    await favorites_module.add_favorite(user.id, track)

    await favorites_module.remove_favorite(user.id, track["deezer_track_id"])

    result = await favorites_module.is_track_favorite(user.id, track["deezer_track_id"])
    assert result is False


# ── get_favorite_tracks ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_favorite_tracks_returns_joined_dict_ordered(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    await favorites_module.add_favorite(user.id, make_track(deezer_track_id="fav_a", title="Alpha"))
    await favorites_module.add_favorite(user.id, make_track(deezer_track_id="fav_b", title="Beta"))

    favorites = await favorites_module.get_favorite_tracks(user.id)

    assert len(favorites) == 2
    assert "favorite_created_at" in favorites[0]
    assert favorites[0]["title"] == "Beta"


# ── clear_favorites ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_favorites_empties_all(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await favorites_module.add_favorite(user.id, make_track(deezer_track_id="fav_c"))
    await favorites_module.add_favorite(user.id, make_track(deezer_track_id="fav_d"))

    await favorites_module.clear_favorites(user.id)

    favorites = await favorites_module.get_favorite_tracks(user.id)
    assert favorites == []


@pytest.mark.asyncio
async def test_add_favorite_unknown_user_is_noop(live_pg):
    track = make_track()
    await favorites_module.add_favorite(99999, track)

    async with live_pg.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM favorites")
    assert count == 0
