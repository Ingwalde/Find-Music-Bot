from types import SimpleNamespace

from app.services import lyrics_service


class FakeGeniusClient:
    def __init__(self, token, timeout):
        self.token = token
        self.timeout = timeout
        self.verbose = True
        self.remove_section_headers = False
        self.skip_non_songs = False

    def search_song(self, title, artist=None):
        return SimpleNamespace(url=f"https://genius.com/{artist}-{title}")


def test_create_genius_client_returns_none_without_token(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", None)

    assert lyrics_service.create_genius_client() is None


def test_create_genius_client_configures_optional_flags(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")
    monkeypatch.setattr(lyrics_service.lyricsgenius, "Genius", FakeGeniusClient)

    client = lyrics_service.create_genius_client()

    assert client.token == "token"
    assert client.timeout == 10
    assert client.verbose is False
    assert client.remove_section_headers is True
    assert client.skip_non_songs is True


def test_create_genius_client_handles_library_error(monkeypatch):
    monkeypatch.setattr(lyrics_service.settings, "GENIUS_TOKEN", "token")

    def raise_error(*args, **kwargs):
        raise RuntimeError("Genius unavailable")

    monkeypatch.setattr(lyrics_service.lyricsgenius, "Genius", raise_error)

    assert lyrics_service.create_genius_client() is None


def test_find_lyrics_url_returns_none_when_client_is_missing(monkeypatch):
    monkeypatch.setattr(lyrics_service, "get_genius_client", lambda: None)

    assert lyrics_service.find_lyrics_url("SOS", "ABBA") is None


def test_find_lyrics_url_returns_song_url(monkeypatch):
    client = FakeGeniusClient("token", timeout=10)
    monkeypatch.setattr(lyrics_service, "get_genius_client", lambda: client)

    url = lyrics_service.find_lyrics_url("SOS", "ABBA")

    assert url == "https://genius.com/ABBA-SOS"


def test_find_lyrics_url_returns_none_when_song_not_found(monkeypatch):
    client = FakeGeniusClient("token", timeout=10)
    client.search_song = lambda title, artist=None: None
    monkeypatch.setattr(lyrics_service, "get_genius_client", lambda: client)

    assert lyrics_service.find_lyrics_url("Unknown", "Unknown") is None


def test_find_lyrics_url_handles_search_error(monkeypatch):
    client = FakeGeniusClient("token", timeout=10)

    def raise_error(title, artist=None):
        raise RuntimeError("request failed")

    client.search_song = raise_error
    monkeypatch.setattr(lyrics_service, "get_genius_client", lambda: client)

    assert lyrics_service.find_lyrics_url("SOS", "ABBA") is None


def test_get_genius_client_is_lazy(monkeypatch):
    calls = {"count": 0}

    def fake_create_client():
        calls["count"] += 1
        return FakeGeniusClient("token", timeout=10)

    lyrics_service.reset_genius_client()
    monkeypatch.setattr(lyrics_service, "create_genius_client", fake_create_client)

    assert lyrics_service.get_genius_client() is lyrics_service.get_genius_client()
    assert calls["count"] == 1

    lyrics_service.reset_genius_client()
