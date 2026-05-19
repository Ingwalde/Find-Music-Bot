import pytest
import requests
from requests import HTTPError

from app.platforms.spotify import auth, client


@pytest.fixture(autouse=True)
def reset_spotify_runtime_state():
    auth.reset_spotify_runtime_state()
    yield
    auth.reset_spotify_runtime_state()


class FakeHttpResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            error = HTTPError(f"{self.status_code} error")
            error.response = self
            raise error

    def json(self):
        return self.payload


def test_handle_spotify_http_error_raises_credentials_error_for_401():
    error = HTTPError("401")
    error.response = FakeHttpResponse(status_code=401)

    with pytest.raises(auth.SpotifyCredentialsError):
        auth.handle_spotify_http_error(error, "token request")


def test_handle_spotify_http_error_reraises_unknown_http_error():
    error = HTTPError("500")
    error.response = FakeHttpResponse(status_code=500)

    with pytest.raises(HTTPError):
        auth.handle_spotify_http_error(error, "token request")


def test_get_spotify_access_token_returns_cached_token(monkeypatch):
    calls = []

    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(
        auth.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or FakeHttpResponse(payload={"access_token": "token-1", "expires_in": 3600}),
    )

    assert auth.get_spotify_access_token() == "token-1"
    assert auth.get_spotify_access_token() == "token-1"
    assert len(calls) == 1


def test_get_spotify_access_token_returns_none_on_request_exception(monkeypatch):
    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(
        auth.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.RequestException("network down")),
    )

    assert auth.get_spotify_access_token() is None


def test_get_spotify_access_token_returns_none_on_401(monkeypatch):
    monkeypatch.setattr(auth.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth.settings, "SPOTIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(auth.requests, "post", lambda *args, **kwargs: FakeHttpResponse(status_code=401))

    assert auth.get_spotify_access_token() is None


def test_request_spotify_search_success_without_market(monkeypatch):
    captured = {}
    items = [{"id": "spotify-id"}]

    def fake_get(*args, **kwargs):
        captured.update(kwargs)
        return FakeHttpResponse(payload={"tracks": {"items": items}})

    monkeypatch.setattr(client.requests, "get", fake_get)

    result = client.request_spotify_search(
        token="token",
        query="ABBA SOS",
        limit=3,
        market=None,
    )

    assert result == items
    assert captured["params"] == {"q": "ABBA SOS", "type": "track", "limit": 3}


def test_request_spotify_search_returns_empty_on_request_exception(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.RequestException("timeout")),
    )

    assert client.request_spotify_search("token", "ABBA", 5, "NO") == []


def test_search_spotify_track_returns_best_candidate(monkeypatch):
    monkeypatch.setattr(client, "get_spotify_access_token", lambda: "token")
    monkeypatch.setattr(client.settings, "SPOTIFY_MARKET", "NO")
    monkeypatch.setattr(
        client,
        "request_spotify_search",
        lambda **kwargs: [
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
        ],
    )

    result = client.search_spotify_track("SOS", "ABBA")

    assert result["spotify_track_id"] == "good"
    assert result["spotify_link"].endswith("/good")


def test_search_spotify_track_ignores_candidates_without_links(monkeypatch):
    monkeypatch.setattr(client, "get_spotify_access_token", lambda: "token")
    monkeypatch.setattr(
        client,
        "request_spotify_search",
        lambda **kwargs: [
            {
                "id": "no-link",
                "name": "SOS",
                "artists": [{"name": "ABBA"}],
                "album": {"name": "Album"},
                "external_urls": {},
            }
        ],
    )

    assert client.search_spotify_track("SOS", "ABBA") is None
