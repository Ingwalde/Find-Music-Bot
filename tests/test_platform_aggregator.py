import pytest

from app.platforms import aggregator
from app.platforms.spotify.auth import SpotifyForbiddenError


@pytest.mark.asyncio
async def test_spotify_forbidden_returns_original_track(monkeypatch):
    track = {
        "deezer_track_id": "123",
        "title": "SOS",
        "artist": "ABBA",
        "deezer_link": "https://deezer.example/track/123",
    }

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")

    async def fake_get_spotify_data(_track_id):
        return None

    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", fake_get_spotify_data)

    async def raise_forbidden(*args, **kwargs):
        raise SpotifyForbiddenError("403 Forbidden")

    monkeypatch.setattr(aggregator, "search_spotify_track", raise_forbidden)

    result = await aggregator.enrich_track_with_platform_links(track.copy())

    assert result["deezer_track_id"] == "123"
    assert "spotify_link" not in result


@pytest.mark.asyncio
async def test_cached_spotify_link_is_added(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")

    async def fake_get_spotify_data(_track_id):
        return {
            "spotify_track_id": "spotify123",
            "spotify_link": "https://open.spotify.com/track/spotify123",
        }

    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", fake_get_spotify_data)

    result = await aggregator.enrich_track_with_platform_links(track.copy())

    assert result["spotify_track_id"] == "spotify123"
    assert result["spotify_link"] == "https://open.spotify.com/track/spotify123"
