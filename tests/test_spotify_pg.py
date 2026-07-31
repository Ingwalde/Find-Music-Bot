"""
Integration tests for async PostgreSQL spotify.py repository.
Uses the compose "test-postgres" service via the shared live_pg fixture from conftest.py.

spotify.py reads/writes the tracks table, so each test that needs
an existing track saves one via tracks_module first.
"""

import pytest

import app.database.repository_modules.spotify as spotify_module
import app.database.repository_modules.tracks as tracks_module

DEEZER_ID = "spotify_test_track_001"


def make_track(deezer_track_id=DEEZER_ID):
    return {
        "deezer_track_id": deezer_track_id,
        "title": "Spotify Test Song",
        "artist": "Spotify Artist",
        "album": "Spotify Album",
        "duration": "03:00",
        "duration_seconds": 180,
        "deezer_link": f"https://www.deezer.com/track/{deezer_track_id}",
        "cover_url": "https://e-cdns-images.dzcdn.net/images/cover/sp.jpg",
        "release_date": "2021-05-01",
        "rank": 600000,
        "popularity": "Medium",
    }


@pytest.mark.asyncio
async def test_get_spotify_data_returns_none_for_missing_track(live_pg):
    result = await spotify_module.get_spotify_data_by_deezer_id("no_such_track")
    assert result is None


@pytest.mark.asyncio
async def test_get_spotify_data_returns_none_without_spotify_link(live_pg):
    await tracks_module.save_track(make_track())

    result = await spotify_module.get_spotify_data_by_deezer_id(DEEZER_ID)
    assert result is None


@pytest.mark.asyncio
async def test_update_then_get_returns_correct_data(live_pg):
    await tracks_module.save_track(make_track())

    await spotify_module.update_spotify_data_for_track(
        deezer_track_id=DEEZER_ID,
        spotify_track_id="sp_123",
        spotify_link="https://open.spotify.com/track/sp_123",
    )

    result = await spotify_module.get_spotify_data_by_deezer_id(DEEZER_ID)

    assert result is not None
    assert result["spotify_track_id"] == "sp_123"
    assert result["spotify_link"] == "https://open.spotify.com/track/sp_123"


@pytest.mark.asyncio
async def test_update_sets_spotify_updated_at(live_pg):
    await tracks_module.save_track(make_track())

    await spotify_module.update_spotify_data_for_track(
        deezer_track_id=DEEZER_ID,
        spotify_track_id="sp_456",
        spotify_link="https://open.spotify.com/track/sp_456",
    )

    result = await spotify_module.get_spotify_data_by_deezer_id(DEEZER_ID)
    assert result["spotify_updated_at"] is not None
