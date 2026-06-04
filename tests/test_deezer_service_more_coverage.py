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




class FakeDeezerClient:
    def __init__(self, search_result=None, track_result=None):
        self.search_result = search_result if search_result is not None else []
        self.track_result = track_result

    def search(self, query):
        if isinstance(self.search_result, Exception):
            raise self.search_result
        return self.search_result

    def get_track(self, track_id):
        if isinstance(self.track_result, Exception):
            raise self.track_result
        return self.track_result or make_track(id=track_id)


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
        deezer_service,
        "get_deezer_client",
        lambda: FakeDeezerClient(search_result=RuntimeError("deezer unavailable")),
    )

    assert deezer_service.search_tracks("ABBA") == []


def test_search_tracks_skips_tracks_that_cannot_be_formatted(monkeypatch):
    valid_track = make_track()
    invalid_track = SimpleNamespace()

    monkeypatch.setattr(
        deezer_service,
        "get_deezer_client",
        lambda: FakeDeezerClient(search_result=[invalid_track, valid_track]),
    )

    results = deezer_service.search_tracks("ABBA", limit=5)

    assert len(results) == 1
    assert results[0]["title"] == "SOS"


def test_search_tracks_respects_limit(monkeypatch):
    tracks = [make_track(id=index, title=f"Track {index}") for index in range(5)]
    monkeypatch.setattr(
        deezer_service,
        "get_deezer_client",
        lambda: FakeDeezerClient(search_result=tracks),
    )

    results = deezer_service.search_tracks("ABBA", limit=2)

    assert [track["title"] for track in results] == ["Track 0", "Track 1"]


def test_get_track_success(monkeypatch):
    monkeypatch.setattr(
        deezer_service,
        "get_deezer_client",
        lambda: FakeDeezerClient(track_result=make_track(id=123)),
    )

    result = deezer_service.get_track("123")

    assert result["deezer_track_id"] == "123"


def test_get_track_wraps_deezer_errors(monkeypatch):
    monkeypatch.setattr(
        deezer_service,
        "get_deezer_client",
        lambda: FakeDeezerClient(track_result=RuntimeError("not found")),
    )

    with pytest.raises(RuntimeError, match="Could not load Deezer track"):
        deezer_service.get_track("bad")
