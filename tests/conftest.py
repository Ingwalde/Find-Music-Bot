import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def make_httpx_response(status_code: int = 200, json_data: dict | None = None) -> httpx.Response:
    """
    Builds a real httpx.Response for mocking AsyncClient calls in tests.
    Using a real Response means .raise_for_status() and .json() behave exactly
    like production code, including raising httpx.HTTPStatusError on 4xx/5xx.
    """
    request = httpx.Request("GET", "https://example.com")
    return httpx.Response(status_code, request=request, json=json_data if json_data is not None else {})


class FakeAsyncClient:
    """
    Minimal async context-manager stand-in for httpx.AsyncClient.

    Returns a fixed response (or raises a fixed exception) for every
    get()/post() call, regardless of arguments. If `responses` is given,
    each call pops the next response from that list instead (useful for
    code paths that issue multiple sequential requests).
    """

    def __init__(
        self,
        response: httpx.Response | None = None,
        responses: list[httpx.Response] | None = None,
        exc: Exception | None = None,
    ):
        self.response = response
        self.responses = responses
        self.exc = exc
        self.calls: list[tuple[str, tuple, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def _respond(self, method: str, args: tuple, kwargs: dict) -> httpx.Response:
        self.calls.append((method, args, kwargs))
        if self.exc is not None:
            raise self.exc
        if self.responses is not None:
            return self.responses.pop(0)
        return self.response

    async def get(self, *args, **kwargs):
        return await self._respond("get", args, kwargs)

    async def post(self, *args, **kwargs):
        return await self._respond("post", args, kwargs)


@pytest.fixture
def fake_user():
    """
    Returns a lightweight object compatible with repositories.upsert_user().
    """
    return SimpleNamespace(
        id=123456789,
        username="test_user",
        first_name="Test",
    )


@pytest.fixture
def sample_track():
    """
    Returns normalized track dictionary used by database and formatter tests.
    """
    return {
        "deezer_track_id": "671298",
        "title": "Music & Me",
        "artist": "Nate Dogg",
        "album": "Music and Me",
        "duration": "04:00",
        "duration_seconds": 240,
        "deezer_link": "https://www.deezer.com/track/671298",
        "cover_url": "https://e-cdns-images.dzcdn.net/images/cover/test.jpg",
        "release_date": "2001-12-04",
        "rank": 789123,
        "popularity": "Very high",
    }


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    """
    Configures the app to use an isolated SQLite database for each test.
    """
    from app.config.settings import settings
    from app.database.db import init_db

    db_path = tmp_path / "test_music_bot.db"

    monkeypatch.setattr(settings, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(settings, "MAX_HISTORY_PER_USER", 5)
    monkeypatch.setattr(settings, "HISTORY_LIMIT", 3)

    init_db()

    return db_path


def to_async(fn):
    """
    Wraps a sync callable into an async one, for monkeypatching await-ed functions.
    """

    async def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def fake_message(text: str = "SOS", user_id: int = 123):
    """
    Minimal aiogram-compatible Message stand-in for handler tests.
    """
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        chat=SimpleNamespace(id=10),
    )


def fake_call(data: str = "noop", user_id: int = 123):
    """
    Minimal aiogram-compatible CallbackQuery stand-in for callback handler tests.
    """
    return SimpleNamespace(
        id="call-id",
        data=data,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        message=SimpleNamespace(chat=SimpleNamespace(id=10), message_id=20),
    )


class AsyncFakeBot:
    """
    Async stand-in for aiogram.Bot used by async callback handler tests.
    """

    def __init__(self):
        self.answers = []
        self.messages = []
        self.edited_texts = []
        self.edited_markups = []
        self.photos = []
        self.raise_on_edit = False
        self.raise_on_photo = False

    async def answer_callback_query(self, *args, **kwargs):
        self.answers.append((args, kwargs))

    async def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))

    async def edit_message_text(self, *args, **kwargs):
        if self.raise_on_edit:
            raise RuntimeError("edit failed")
        self.edited_texts.append((args, kwargs))

    async def edit_message_reply_markup(self, *args, **kwargs):
        if self.raise_on_edit:
            raise RuntimeError("edit failed")
        self.edited_markups.append((args, kwargs))

    async def send_photo(self, *args, **kwargs):
        if self.raise_on_photo:
            raise RuntimeError("photo failed")
        self.photos.append((args, kwargs))


@pytest.fixture(autouse=True)
def clear_search_contexts():
    """
    Clears in-memory pagination/search contexts between tests.
    """
    from app.bot.context import search_contexts

    search_contexts.clear()
    yield
    search_contexts.clear()
