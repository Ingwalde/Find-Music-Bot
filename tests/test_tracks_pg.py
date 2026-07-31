"""
Integration tests for async PostgreSQL tracks.py repository.
Uses the compose "test-postgres" service via the shared live_pg fixture from conftest.py.
"""

import pytest

import app.database.repository_modules.tracks as tracks_module


def make_track(
    deezer_track_id="671298",
    title="Music & Me",
    artist="Nate Dogg",
    album="Music and Me",
    duration="04:00",
    duration_seconds=240,
    deezer_link="https://www.deezer.com/track/671298",
    cover_url="https://e-cdns-images.dzcdn.net/images/cover/test.jpg",
    release_date="2001-12-04",
    rank=789123,
    popularity="Very high",
):
    return {
        "deezer_track_id": deezer_track_id,
        "title": title,
        "artist": artist,
        "album": album,
        "duration": duration,
        "duration_seconds": duration_seconds,
        "deezer_link": deezer_link,
        "cover_url": cover_url,
        "release_date": release_date,
        "rank": rank,
        "popularity": popularity,
    }


# ── save_track ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_track_inserts_and_returns_id(live_pg):
    track_id = await tracks_module.save_track(make_track())

    assert isinstance(track_id, int)
    assert track_id > 0


@pytest.mark.asyncio
async def test_save_track_on_conflict_returns_same_id(live_pg):
    track = make_track()
    first_id = await tracks_module.save_track(track)
    second_id = await tracks_module.save_track(track)

    assert first_id == second_id


@pytest.mark.asyncio
async def test_save_track_on_conflict_updates_metadata(live_pg):
    await tracks_module.save_track(make_track(title="Original Title", rank=100))
    await tracks_module.save_track(make_track(title="Updated Title", rank=200))

    result = await tracks_module.get_track_by_deezer_id("671298")
    assert result["title"] == "Updated Title"
    assert result["rank"] == 200


# ── get_track_by_deezer_id ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_track_by_deezer_id_returns_full_dict(live_pg):
    track = make_track()
    await tracks_module.save_track(track)

    result = await tracks_module.get_track_by_deezer_id(track["deezer_track_id"])

    assert result is not None
    assert result["title"] == "Music & Me"
    assert result["artist"] == "Nate Dogg"
    assert result["rank"] == 789123
    assert "updated_at" in result
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_track_by_deezer_id_returns_none_for_unknown(live_pg):
    result = await tracks_module.get_track_by_deezer_id("nonexistent_id")
    assert result is None


# ── get_tracks_by_artist ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_tracks_by_artist_returns_matching_tracks(live_pg):
    await tracks_module.save_track(make_track(deezer_track_id="aaa", title="Track A", rank=500))
    await tracks_module.save_track(make_track(deezer_track_id="bbb", title="Track B", rank=300))

    results = await tracks_module.get_tracks_by_artist(
        artist="Nate Dogg",
        exclude_deezer_id="none",
        limit=5,
    )

    ids = [r["deezer_track_id"] for r in results]
    assert "aaa" in ids
    assert "bbb" in ids


@pytest.mark.asyncio
async def test_get_tracks_by_artist_excludes_given_track(live_pg):
    track = make_track()
    await tracks_module.save_track(track)

    results = await tracks_module.get_tracks_by_artist(
        artist="Nate Dogg",
        exclude_deezer_id=track["deezer_track_id"],
        limit=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_get_tracks_by_artist_returns_empty_for_unknown_artist(live_pg):
    results = await tracks_module.get_tracks_by_artist(
        artist="No Such Artist",
        exclude_deezer_id="0",
    )
    assert results == []


@pytest.mark.asyncio
async def test_get_tracks_by_artist_orders_by_rank_descending(live_pg):
    await tracks_module.save_track(make_track(deezer_track_id="low", title="Low", rank=100))
    await tracks_module.save_track(make_track(deezer_track_id="high", title="High", rank=9000))

    results = await tracks_module.get_tracks_by_artist(
        artist="Nate Dogg",
        exclude_deezer_id="none",
        limit=5,
    )

    assert results[0]["deezer_track_id"] == "high"
