import pytest

from app.services import spotify_service
from app.services.spotify_service import (
    SpotifyForbiddenError,
    build_spotify_queries,
    disable_spotify_temporarily,
    format_spotify_track,
    get_spotify_block_reason,
    is_spotify_temporarily_blocked,
    normalize_text,
    reset_spotify_runtime_state,
    score_spotify_candidate,
)


@pytest.fixture(autouse=True)
def reset_spotify_state():
    reset_spotify_runtime_state()
    yield
    reset_spotify_runtime_state()


def test_normalize_text():
    assert normalize_text(" Music & Me! ") == "music me"


def test_build_spotify_queries_with_title_and_artist():
    assert build_spotify_queries("SOS", "ABBA") == [
        'track:"SOS" artist:"ABBA"',
        "SOS ABBA",
        "SOS",
    ]


def test_build_spotify_queries_with_only_title():
    assert build_spotify_queries("SOS", None) == ["SOS"]


def test_format_spotify_track():
    item = {
        "id": "spotify123",
        "name": "Music & Me",
        "artists": [{"name": "Nate Dogg"}],
        "album": {"name": "Music and Me"},
        "external_urls": {"spotify": "https://open.spotify.com/track/spotify123"},
    }

    result = format_spotify_track(item)

    assert result["spotify_track_id"] == "spotify123"
    assert result["spotify_title"] == "Music & Me"
    assert result["spotify_artist"] == "Nate Dogg"
    assert result["spotify_album"] == "Music and Me"
    assert result["spotify_link"] == "https://open.spotify.com/track/spotify123"


def test_score_spotify_candidate_prefers_similar_track():
    candidate = {
        "spotify_title": "Music & Me",
        "spotify_artist": "Nate Dogg",
    }

    score = score_spotify_candidate(candidate, "Music & Me", "Nate Dogg")

    assert score > 0.9


def test_disable_spotify_temporarily(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS", 3600)

    disable_spotify_temporarily("403 Forbidden")

    assert is_spotify_temporarily_blocked() is True
    assert get_spotify_block_reason() == "403 Forbidden"


def test_search_spotify_track_skips_when_temporarily_blocked(monkeypatch):
    monkeypatch.setattr(spotify_service, "get_spotify_access_token", lambda: None)

    assert spotify_service.search_spotify_track("SOS", "ABBA") is None
