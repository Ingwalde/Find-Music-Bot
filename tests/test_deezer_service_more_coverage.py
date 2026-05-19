from types import SimpleNamespace

import pytest

from app.services import deezer_service


def make_track(**overrides):
    values = {
        "id": 1,
        "title": "SOS",
        "artist": SimpleNamespace(name="ABBA"),
        "album": SimpleNamespace(title="ABBA Gold", cover="https://example.com/cover.jpg"),
        "duration": 210,
        "link": "https://www.deezer.com/track/1",
        "release_date": None,
        "rank": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_get_object_value_returns_string_objects_as_is():
    assert deezer_service.get_object_value("ABBA", ["name"]) == "ABBA"


def test_format_deezer_track_handles_missing_album_cover_and_rank():
    track = make_track(album=None, artist="ABBA")

    result = deezer_service.format_deezer_track(track)

    assert result["artist"] == "ABBA"
    assert result["album"] == "Unknown album"
    assert result["cover_url"] is None
    assert result["rank"] is None
    assert result["popularity"] is None


def test_search_tracks_returns_empty_for_blank_query():
    assert deezer_service.search_tracks("   ") == []


def test_search_tracks_returns_empty_when_deezer_fails(monkeypatch):
    monkeypatch.setattr(
        deezer_service.client,
        "search",
        lambda query: (_ for _ in ()).throw(RuntimeError("deezer unavailable")),
    )

    assert deezer_service.search_tracks("ABBA") == []


def test_search_tracks_skips_tracks_that_cannot_be_formatted(monkeypatch):
    valid_track = make_track()
    invalid_track = SimpleNamespace()

    monkeypatch.setattr(deezer_service.client, "search", lambda query: [invalid_track, valid_track])

    results = deezer_service.search_tracks("ABBA", limit=5)

    assert len(results) == 1
    assert results[0]["title"] == "SOS"


def test_search_tracks_respects_limit(monkeypatch):
    tracks = [make_track(id=index, title=f"Track {index}") for index in range(5)]
    monkeypatch.setattr(deezer_service.client, "search", lambda query: tracks)

    results = deezer_service.search_tracks("ABBA", limit=2)

    assert [track["title"] for track in results] == ["Track 0", "Track 1"]


def test_get_track_success(monkeypatch):
    monkeypatch.setattr(deezer_service.client, "get_track", lambda track_id: make_track(id=track_id))

    result = deezer_service.get_track("123")

    assert result["deezer_track_id"] == "123"


def test_get_track_wraps_deezer_errors(monkeypatch):
    monkeypatch.setattr(
        deezer_service.client,
        "get_track",
        lambda track_id: (_ for _ in ()).throw(RuntimeError("not found")),
    )

    with pytest.raises(RuntimeError, match="Could not load Deezer track"):
        deezer_service.get_track("bad")
