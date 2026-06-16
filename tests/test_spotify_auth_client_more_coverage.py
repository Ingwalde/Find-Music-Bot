import asyncio

import httpx
import pytest

from app.platforms.spotify import auth, client
from tests.conftest import FakeAsyncClient, make_httpx_response


@pytest.fixture(autouse=True)
def reset_spotify_runtime_state():
    auth.reset_spotify_runtime_state()
    yield
    auth.reset_spotify_runtime_state()


def test_handle_spotify_http_error_raises_credentials_error_for_401():
    response = make_httpx_response(status_code=401)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        response.raise_for_status()

    with pytest.raises(auth.SpotifyCredentialsError):
        auth.handle_spotify_http_error(exc_info.value, "token request")


def test_handle_spotify_http_error_reraises_unknown_http_error():
    response = make_httpx_response(status_code=500)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        response.raise_for_status()

    with pytest.raises(httpx.HTTPStatusError):
        auth.handle_spotify_http_error(exc_info.value, "token request")


@pytest.mark.asyncio
async def test_get_spotify_access_token_returns_cached_token(monkeypatch):
    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")

    fake_client = FakeAsyncClient(
        response=make_httpx_response(json_data={"access_token": "token-1", "expires_in": 3600})
    )
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await auth.get_spotify_access_token() == "token-1"
    assert await auth.get_spotify_access_token() == "token-1"
    assert len(fake_client.calls) == 1


@pytest.mark.asyncio
async def test_get_spotify_access_token_returns_none_on_request_exception(monkeypatch):
    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")

    fake_client = FakeAsyncClient(exc=httpx.ConnectError("network down"))
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await auth.get_spotify_access_token() is None


@pytest.mark.asyncio
async def test_get_spotify_access_token_returns_none_on_401(monkeypatch):
    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")

    fake_client = FakeAsyncClient(response=make_httpx_response(status_code=401))
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await auth.get_spotify_access_token() is None


@pytest.mark.asyncio
async def test_request_spotify_search_success_without_market(monkeypatch):
    items = [{"id": "spotify-id"}]
    fake_client = FakeAsyncClient(response=make_httpx_response(json_data={"tracks": {"items": items}}))
    monkeypatch.setattr(client.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    result = await client.request_spotify_search(
        token="token",
        query="ABBA SOS",
        limit=3,
        market=None,
    )

    assert result == items
    _, _, kwargs = fake_client.calls[0]
    assert kwargs["params"] == {"q": "ABBA SOS", "type": "track", "limit": 3}


@pytest.mark.asyncio
async def test_request_spotify_search_returns_empty_on_request_exception(monkeypatch):
    fake_client = FakeAsyncClient(exc=httpx.ConnectError("timeout"))
    monkeypatch.setattr(client.httpx, "AsyncClient", lambda *args, **kwargs: fake_client)

    assert await client.request_spotify_search("token", "ABBA", 5, "NO") == []


@pytest.mark.asyncio
async def test_search_spotify_track_returns_best_candidate(monkeypatch):
    async def fake_get_token():
        return "token"

    async def fake_search(**kwargs):
        return [
            {
                "id": "bad",
                "name": "Different Song",
                "artists": [{"name": "Other Artist"}],
                "album": {"name": "Other Album"},
                "external_urls": {"spotify": "https://open.spotify.com/track/bad"},
            },
            {
                "id": "good",
                "name": "SOS",
                "artists": [{"name": "ABBA"}],
                "album": {"name": "ABBA Gold"},
                "external_urls": {"spotify": "https://open.spotify.com/track/good"},
            },
        ]

    monkeypatch.setattr(client, "get_spotify_access_token", fake_get_token)
    monkeypatch.setattr(client.settings, "SPOTIFY_MARKET", "NO")
    monkeypatch.setattr(client, "request_spotify_search", fake_search)

    result = await client.search_spotify_track("SOS", "ABBA")

    assert result["spotify_track_id"] == "good"
    assert result["spotify_link"].endswith("/good")


@pytest.mark.asyncio
async def test_search_spotify_track_ignores_candidates_without_links(monkeypatch):
    async def fake_get_token():
        return "token"

    async def fake_search(**kwargs):
        return [
            {
                "id": "no-link",
                "name": "SOS",
                "artists": [{"name": "ABBA"}],
                "album": {"name": "Album"},
                "external_urls": {},
            }
        ]

    monkeypatch.setattr(client, "get_spotify_access_token", fake_get_token)
    monkeypatch.setattr(client, "request_spotify_search", fake_search)

    assert await client.search_spotify_track("SOS", "ABBA") is None


@pytest.mark.asyncio
async def test_spotify_runtime_lock_is_asyncio_lock():
    assert isinstance(auth._spotify_runtime_lock, asyncio.Lock)

    async with auth._spotify_runtime_lock:
        auth.disable_spotify_temporarily("blocked")
        assert auth.is_spotify_temporarily_blocked() is True
        assert auth.get_spotify_block_reason() == "blocked"
