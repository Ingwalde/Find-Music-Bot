from app.platforms import aggregator
from app.platforms.spotify.auth import SpotifyCredentialsError


def test_enrichment_skips_when_spotify_disabled(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", False)

    assert aggregator.enrich_track_with_platform_links(track.copy()) == track


def test_enrichment_skips_without_deezer_track_id(monkeypatch):
    track = {"title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")

    assert aggregator.enrich_track_with_platform_links(track.copy()) == track


def test_enrichment_adds_new_spotify_match_and_updates_cache(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}
    updated_cache = {}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", lambda _track_id: None)
    monkeypatch.setattr(
        aggregator,
        "search_spotify_track",
        lambda **kwargs: {
            "spotify_track_id": "spotify123",
            "spotify_link": "https://open.spotify.com/track/spotify123",
        },
    )

    def fake_update(**kwargs):
        updated_cache.update(kwargs)

    monkeypatch.setattr(aggregator, "update_spotify_data_for_track", fake_update)

    result = aggregator.enrich_track_with_platform_links(track.copy())

    assert result["spotify_track_id"] == "spotify123"
    assert result["spotify_link"] == "https://open.spotify.com/track/spotify123"
    assert updated_cache == {
        "deezer_track_id": "123",
        "spotify_track_id": "spotify123",
        "spotify_link": "https://open.spotify.com/track/spotify123",
    }


def test_enrichment_returns_original_track_when_no_spotify_match(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", lambda _track_id: None)
    monkeypatch.setattr(aggregator, "search_spotify_track", lambda **kwargs: None)

    result = aggregator.enrich_track_with_platform_links(track.copy())

    assert result == track


def test_enrichment_handles_spotify_credentials_error(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", lambda _track_id: None)

    def raise_credentials_error(**kwargs):
        raise SpotifyCredentialsError("bad credentials")

    monkeypatch.setattr(aggregator, "search_spotify_track", raise_credentials_error)

    result = aggregator.enrich_track_with_platform_links(track.copy())

    assert result == track


def test_enrichment_handles_unexpected_error(monkeypatch):
    track = {"deezer_track_id": "123", "title": "SOS", "artist": "ABBA"}

    monkeypatch.setattr(aggregator.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_ID", "client")
    monkeypatch.setattr(aggregator.settings, "SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(aggregator, "get_spotify_data_by_deezer_id", lambda _track_id: None)

    def raise_runtime_error(**kwargs):
        raise RuntimeError("network timeout")

    monkeypatch.setattr(aggregator, "search_spotify_track", raise_runtime_error)

    result = aggregator.enrich_track_with_spotify_link(track.copy())

    assert result == track
