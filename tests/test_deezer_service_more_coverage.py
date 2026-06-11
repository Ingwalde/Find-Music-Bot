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


def make_raw_track(track_id=1, title="SOS", artist_name="ABBA", duration=210):
    return {
        "id": track_id,
        "title": title,
        "artist": {"name": artist_name},
        "album": {"title": "Gold", "cover_xl": "https://cdn.deezer.com/cover.jpg"},
        "duration": duration,
        "link": f"https://www.deezer.com/track/{track_id}",
        "rank": 500000,
    }


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_get_trending_tracks_returns_list_on_success(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": [make_raw_track(3, "Dancing Queen")]}),
    )

    result = deezer_service.get_trending_tracks()

    assert len(result) == 1
    assert result[0]["title"] == "Dancing Queen"


def test_get_trending_tracks_returns_empty_on_request_error(monkeypatch):
    def failing_get(url, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr(deezer_service.requests, "get", failing_get)

    result = deezer_service.get_trending_tracks()

    assert result == []


def test_get_artist_top_tracks_returns_tracks(monkeypatch):
    artist_response = FakeResponse({"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]})
    top_response = FakeResponse({"data": [make_raw_track(10, "Mamma Mia")]})
    responses = [artist_response, top_response]

    monkeypatch.setattr(deezer_service.requests, "get", lambda url, **kwargs: responses.pop(0))

    result = deezer_service.get_artist_top_tracks("ABBA", limit=1)

    assert len(result) == 1
    assert result[0]["title"] == "Mamma Mia"


def test_get_artist_top_tracks_returns_empty_when_artist_not_found(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": []}),
    )

    result = deezer_service.get_artist_top_tracks("Unknown Artist XYZ")

    assert result == []


def test_get_artist_top_tracks_returns_empty_on_search_error(monkeypatch):
    def failing_get(url, **kwargs):
        raise RuntimeError("search failed")

    monkeypatch.setattr(deezer_service.requests, "get", failing_get)

    result = deezer_service.get_artist_top_tracks("ABBA")

    assert result == []


def test_get_artist_top_tracks_returns_empty_on_top_error(monkeypatch):
    artist_response = FakeResponse({"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]})
    call_count = [0]

    def patchy_get(url, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return artist_response
        raise RuntimeError("top endpoint failed")

    monkeypatch.setattr(deezer_service.requests, "get", patchy_get)

    result = deezer_service.get_artist_top_tracks("ABBA")

    assert result == []


def test_parse_raw_track_handles_string_artist_and_missing_album():
    raw = {
        "id": 5,
        "title": "SOS",
        "artist": "ABBA",
        "album": None,
        "duration": 180,
        "link": "https://deezer.com/5",
        "rank": None,
    }

    result = deezer_service._parse_raw_track(raw)

    assert result["artist"] == "ABBA"
    assert result["album"] == "Unknown album"
    assert result["cover_url"] is None


def test_parse_raw_track_handles_null_duration():
    raw = {
        "id": 6,
        "title": "Mamma Mia",
        "artist": {"name": "ABBA"},
        "album": {"title": "Gold"},
        "duration": None,
        "link": "https://deezer.com/6",
        "rank": 400000,
    }

    result = deezer_service._parse_raw_track(raw)

    assert result["duration"] == "00:00"
    assert result["duration_seconds"] == 0
    assert result["title"] == "Mamma Mia"


def test_parse_raw_track_stores_release_date_from_raw():
    raw = {
        "id": 7,
        "title": "Dancing Queen",
        "artist": {"name": "ABBA"},
        "album": {"title": "Arrival"},
        "duration": 230,
        "link": "https://deezer.com/7",
        "rank": 600000,
        "release_date": "1976-10-11",
    }

    result = deezer_service._parse_raw_track(raw)

    assert result["release_date"] == "1976-10-11"


def test_parse_raw_track_release_date_is_none_when_key_missing():
    raw = {
        "id": 8,
        "title": "Fernando",
        "artist": {"name": "ABBA"},
        "album": None,
        "duration": 255,
        "link": "https://deezer.com/8",
        "rank": None,
    }

    result = deezer_service._parse_raw_track(raw)

    assert result["release_date"] is None


def test_parse_raw_track_handles_null_id_and_link():
    raw = {
        "id": None,
        "title": None,
        "artist": {"name": "ABBA"},
        "album": None,
        "duration": 90,
        "link": None,
        "rank": None,
    }

    result = deezer_service._parse_raw_track(raw)

    assert result["deezer_track_id"] == ""
    assert result["title"] == "Unknown"
    assert result["deezer_link"] == ""


def test_get_artist_top_tracks_by_id_returns_tracks(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": [make_raw_track(5, "Fernando")]}),
    )

    result = deezer_service.get_artist_top_tracks_by_id(7, limit=5)

    assert len(result) == 1
    assert result[0]["title"] == "Fernando"
    assert result[0]["artist"] == "ABBA"


def test_get_artist_top_tracks_by_id_returns_empty_on_error(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    result = deezer_service.get_artist_top_tracks_by_id(7)

    assert result == []


def test_get_artist_id_returns_id_on_success(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]}),
    )

    result = deezer_service.get_artist_id("ABBA")

    assert result == 7


def test_get_artist_id_returns_none_when_no_results(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": []}),
    )

    result = deezer_service.get_artist_id("Unknown Artist XYZ")

    assert result is None


def test_get_artist_id_returns_none_on_error(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    result = deezer_service.get_artist_id("ABBA")

    assert result is None


def test_get_related_artists_returns_list_with_limit(monkeypatch):
    artists = [
        {"id": 8, "name": "Queen"},
        {"id": 9, "name": "Led Zeppelin"},
        {"id": 10, "name": "Pink Floyd"},
        {"id": 11, "name": "The Beatles"},
    ]
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: FakeResponse({"data": artists}),
    )

    result = deezer_service.get_related_artists(7, limit=2)

    assert len(result) == 2
    assert result[0] == {"id": 8, "name": "Queen"}


def test_get_related_artists_returns_empty_on_error(monkeypatch):
    monkeypatch.setattr(
        deezer_service.requests,
        "get",
        lambda url, **kwargs: (_ for _ in ()).throw(RuntimeError("network error")),
    )

    result = deezer_service.get_related_artists(7)

    assert result == []
