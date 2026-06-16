import httpx
import pytest

from app.services import lyrics_service
from tests.conftest import FakeAsyncClient, make_httpx_response


def make_genius_payload(url: str | None = None) -> dict:
    hits = []

    if url:
        hits.append({"result": {"url": url}})

    return {"response": {"hits": hits}}


@pytest.mark.asyncio
async def test_find_lyrics_url_returns_none_without_token(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", None)

    assert await lyrics_service.find_lyrics_url("SOS", "ABBA") is None


@pytest.mark.asyncio
async def test_find_lyrics_url_returns_song_url(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")

    fake_client = FakeAsyncClient(
        response=make_httpx_response(json_data=make_genius_payload("https://genius.com/ABBA-SOS"))
    )
    monkeypatch.setattr(lyrics_service.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    url = await lyrics_service.find_lyrics_url("SOS", "ABBA")

    assert url == "https://genius.com/ABBA-SOS"

    _, _, kwargs = fake_client.calls[0]
    assert kwargs["headers"] == {"Authorization": "Bearer token"}
    assert kwargs["params"] == {"q": "ABBA SOS"}


@pytest.mark.asyncio
async def test_find_lyrics_url_returns_none_when_no_hits(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")

    fake_client = FakeAsyncClient(response=make_httpx_response(json_data=make_genius_payload()))
    monkeypatch.setattr(lyrics_service.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await lyrics_service.find_lyrics_url("Unknown", "Unknown") is None


@pytest.mark.asyncio
async def test_find_lyrics_url_handles_request_error(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")

    fake_client = FakeAsyncClient(exc=httpx.ConnectError("request failed"))
    monkeypatch.setattr(lyrics_service.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await lyrics_service.find_lyrics_url("SOS", "ABBA") is None


@pytest.mark.asyncio
async def test_find_lyrics_url_handles_http_status_error(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")

    fake_client = FakeAsyncClient(response=make_httpx_response(status_code=500))
    monkeypatch.setattr(lyrics_service.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await lyrics_service.find_lyrics_url("SOS", "ABBA") is None
