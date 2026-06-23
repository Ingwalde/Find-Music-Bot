import os
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("TESTCONTAINERS_RYUK_CONTAINER_IMAGE", "testcontainers/ryuk:0.11.0")


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


# ── PostgreSQL testcontainers fixtures ────────────────────────────────────────
# Shared by test_users_pg, test_tracks_pg, test_searches_pg (and future modules).
# Stage 10 finalises this fixture set; we consolidate here as modules migrate.


@pytest.fixture(scope="session")
def pg_container():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def pg_dsn(pg_container):
    url = pg_container.get_connection_url()
    return url.replace("+psycopg2", "")


@pytest.fixture(scope="session")
def pg_schema(pg_dsn):
    """
    Builds the PostgreSQL schema ONCE per test session via Alembic's
    baseline revision (alembic upgrade head). Schema setup is owned by
    Alembic exclusively since v3.1.1 — create_tables_pg/create_indexes_pg
    were retired from the app runtime in Stage 4.

    Session-scoped deliberately: running the full Alembic upgrade machinery
    per test function would be needlessly slow across ~69 PG tests. Schema
    build happens once; live_pg (function-scoped) only truncates per test.
    """
    import os

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))

    os.environ["ALEMBIC_DATABASE_URL"] = pg_dsn
    try:
        command.upgrade(cfg, "head")
    finally:
        os.environ.pop("ALEMBIC_DATABASE_URL", None)

    return pg_dsn


@pytest_asyncio.fixture
async def live_pg(pg_schema, monkeypatch):
    """
    Function-scoped asyncpg pool against the testcontainers PostgreSQL instance.
    Schema is built once per session by pg_schema (via Alembic); this fixture
    only truncates per test for isolation and patches get_pool.

    Per-test lifecycle:
      1. Create pool (min_size=1, max_size=3).
      2. TRUNCATE users, tracks RESTART IDENTITY CASCADE
         (cascades to searches and favorites, ensuring a clean slate).
      3. Patch get_pool in every migrated repo module so all DB calls
         use this pool instead of the production singleton.
      4. Yield pool for direct use in assertions.
      5. Close pool on teardown.

    All tests use PostgreSQL — SQLite fixtures removed in Stage 10.
    """
    import asyncpg

    import app.database.maintenance as maintenance_module
    import app.database.repository_modules.errors as errors_module
    import app.database.repository_modules.favorites as favorites_module
    import app.database.repository_modules.searches as searches_module
    import app.database.repository_modules.spotify as spotify_module
    import app.database.repository_modules.tracks as tracks_module
    import app.database.repository_modules.users as users_module
    import app.health as health_module

    pool = await asyncpg.create_pool(pg_schema, min_size=1, max_size=3)

    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE users, tracks, errors, schema_migrations RESTART IDENTITY CASCADE"
        )

    async def _get_pool():
        return pool

    monkeypatch.setattr(users_module, "get_pool", _get_pool)
    monkeypatch.setattr(tracks_module, "get_pool", _get_pool)
    monkeypatch.setattr(searches_module, "get_pool", _get_pool)
    monkeypatch.setattr(favorites_module, "get_pool", _get_pool)
    monkeypatch.setattr(errors_module, "get_pool", _get_pool)
    monkeypatch.setattr(spotify_module, "get_pool", _get_pool)
    monkeypatch.setattr(maintenance_module, "get_pool", _get_pool)
    monkeypatch.setattr(health_module, "get_pool", _get_pool)

    yield pool

    await pool.close()
