import httpx
import pytest

from app.services import deezer_service
from tests.conftest import FakeAsyncClient, make_httpx_response


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


@pytest.mark.asyncio
async def test_search_tracks_returns_empty_for_blank_query():
    assert await deezer_service.search_tracks("   ") == []


@pytest.mark.asyncio
async def test_search_tracks_returns_empty_when_deezer_fails(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("deezer unavailable"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    assert await deezer_service.search_tracks("ABBA") == []


@pytest.mark.asyncio
async def test_search_tracks_returns_parsed_tracks(monkeypatch):
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": [make_raw_track()]}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    results = await deezer_service.search_tracks("ABBA", limit=5)

    assert len(results) == 1
    assert results[0]["title"] == "SOS"
    assert results[0]["artist"] == "ABBA"


@pytest.mark.asyncio
async def test_search_tracks_skips_items_that_cannot_be_parsed(monkeypatch):
    fake_client = FakeAsyncClient(
        response=make_httpx_response(json_data={"data": ["not-a-dict", make_raw_track()]})
    )
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    results = await deezer_service.search_tracks("ABBA", limit=5)

    assert len(results) == 1
    assert results[0]["title"] == "SOS"


@pytest.mark.asyncio
async def test_search_tracks_respects_limit(monkeypatch):
    tracks = [make_raw_track(track_id=index, title=f"Track {index}") for index in range(5)]
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": tracks}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    results = await deezer_service.search_tracks("ABBA", limit=2)

    assert [track["title"] for track in results] == ["Track 0", "Track 1"]


@pytest.mark.asyncio
async def test_get_track_success(monkeypatch):
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data=make_raw_track(track_id=123)))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_track("123")

    assert result["deezer_track_id"] == "123"


@pytest.mark.asyncio
async def test_get_track_wraps_deezer_api_error(monkeypatch):
    fake_client = FakeAsyncClient(
        response=make_httpx_response(json_data={"error": {"message": "no data", "code": 800}})
    )
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    with pytest.raises(RuntimeError, match="Could not load Deezer track"):
        await deezer_service.get_track("bad")


@pytest.mark.asyncio
async def test_get_track_wraps_request_errors(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("not found"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    with pytest.raises(RuntimeError, match="Could not load Deezer track"):
        await deezer_service.get_track("bad")


@pytest.mark.asyncio
async def test_get_trending_tracks_returns_list_on_success(monkeypatch):
    fake_client = FakeAsyncClient(
        response=make_httpx_response(json_data={"data": [make_raw_track(3, "Dancing Queen")]})
    )
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_trending_tracks()

    assert len(result) == 1
    assert result[0]["title"] == "Dancing Queen"


@pytest.mark.asyncio
async def test_get_trending_tracks_returns_empty_on_request_error(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("no network"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_trending_tracks()

    assert result == []


@pytest.mark.asyncio
async def test_get_artist_top_tracks_returns_tracks(monkeypatch):
    artist_response = make_httpx_response(
        json_data={"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]}
    )
    top_response = make_httpx_response(json_data={"data": [make_raw_track(10, "Mamma Mia")]})

    clients = [
        FakeAsyncClient(response=artist_response),
        FakeAsyncClient(response=top_response),
    ]
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: clients.pop(0))

    result = await deezer_service.get_artist_top_tracks("ABBA", limit=1)

    assert len(result) == 1
    assert result[0]["title"] == "Mamma Mia"


@pytest.mark.asyncio
async def test_get_artist_top_tracks_returns_empty_when_artist_not_found(monkeypatch):
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": []}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_top_tracks("Unknown Artist XYZ")

    assert result == []


@pytest.mark.asyncio
async def test_get_artist_top_tracks_returns_empty_on_search_error(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("search failed"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_top_tracks("ABBA")

    assert result == []


@pytest.mark.asyncio
async def test_get_artist_top_tracks_returns_empty_on_top_error(monkeypatch):
    artist_response = make_httpx_response(
        json_data={"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]}
    )

    clients = [
        FakeAsyncClient(response=artist_response),
        FakeAsyncClient(exc=httpx.ConnectError("top endpoint failed")),
    ]
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: clients.pop(0))

    result = await deezer_service.get_artist_top_tracks("ABBA")

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


@pytest.mark.asyncio
async def test_get_artist_top_tracks_by_id_returns_tracks(monkeypatch):
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": [make_raw_track(5, "Fernando")]}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_top_tracks_by_id(7, limit=5)

    assert len(result) == 1
    assert result[0]["title"] == "Fernando"
    assert result[0]["artist"] == "ABBA"


@pytest.mark.asyncio
async def test_get_artist_top_tracks_by_id_returns_empty_on_error(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("timeout"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_top_tracks_by_id(7)

    assert result == []


@pytest.mark.asyncio
async def test_get_artist_id_returns_id_on_success(monkeypatch):
    fake_client = FakeAsyncClient(
        response=make_httpx_response(
            json_data={"data": [{"id": 884025, "title": "Mamma Mia", "artist": {"id": 7, "name": "ABBA"}}]}
        )
    )
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_id("ABBA")

    assert result == 7


@pytest.mark.asyncio
async def test_get_artist_id_returns_none_when_no_results(monkeypatch):
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": []}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_id("Unknown Artist XYZ")

    assert result is None


@pytest.mark.asyncio
async def test_get_artist_id_returns_none_on_error(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("timeout"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_artist_id("ABBA")

    assert result is None


@pytest.mark.asyncio
async def test_get_related_artists_returns_list_with_limit(monkeypatch):
    artists = [
        {"id": 8, "name": "Queen"},
        {"id": 9, "name": "Led Zeppelin"},
        {"id": 10, "name": "Pink Floyd"},
        {"id": 11, "name": "The Beatles"},
    ]
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"data": artists}))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_related_artists(7, limit=2)

    assert len(result) == 2
    assert result[0] == {"id": 8, "name": "Queen"}


@pytest.mark.asyncio
async def test_get_related_artists_returns_empty_on_error(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("network error"))
    monkeypatch.setattr(deezer_service.httpx, "AsyncClient", lambda *a, **kw: fake_client)

    result = await deezer_service.get_related_artists(7)

    assert result == []
