import os
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
import redis.asyncio as aioredis

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
        return SimpleNamespace(message_id=1000 + len(self.messages))

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


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """
    Clears in-memory rate-limit state between tests.

    Without this, the module-level dicts persist across the whole test
    session — many tests call handlers with fake_call()'s default
    user_id=123, so accumulated calls across unrelated tests would
    eventually trip the 20-request limit and break tests that have
    nothing to do with rate limiting.
    """
    from app.bot.rate_limit import _request_timestamps, _warned_users

    _request_timestamps.clear()
    _warned_users.clear()
    yield
    _request_timestamps.clear()
    _warned_users.clear()


@pytest.fixture(autouse=True)
def clear_circuit_breakers():
    """
    Resets per-service circuit breaker state between tests.

    Without this, the module-level dicts in http_retry.py persist across the
    whole test session — a test that intentionally trips a breaker for
    service="deezer" would otherwise leave it open for any later, unrelated
    test that also happens to use that same service key.
    """
    from app.utils.http_retry import reset_circuit_breakers

    reset_circuit_breakers()
    yield
    reset_circuit_breakers()


@pytest.fixture(autouse=True)
def mock_retry_sleep(monkeypatch):
    """
    Replaces asyncio.sleep inside the HTTP retry helper with an instant,
    recording no-op.

    Without this, any test simulating a retryable httpx error (ConnectError,
    TimeoutException, a 5xx response, or 429) — including pre-existing tests
    in test_deezer_service_more_coverage.py, test_lyrics_service.py, and
    test_spotify_auth_client_more_coverage.py that predate the retry helper —
    would incur real 1-5s delays per retry attempt. Autouse so this applies
    everywhere, not just tests written specifically for the retry helper.

    Returns the list of requested pause durations, for tests asserting on
    retry timing (e.g. confirming a 429 used the Retry-After value).
    """
    import app.utils.http_retry as http_retry_module

    sleeps: list[float] = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(http_retry_module.asyncio, "sleep", fake_sleep)
    return sleeps


# ── PostgreSQL integration fixtures ───────────────────────────────────────────
# Shared by all *_pg test modules. Requires DATABASE_URL env var pointing at
# a running postgres instance (locally: docker compose up -d test-postgres).


@pytest.fixture(scope="session")
def pg_dsn() -> str:
    return os.environ["DATABASE_URL"]


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
    Function-scoped asyncpg pool against the PostgreSQL instance at DATABASE_URL.
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
    import app.database.repository_modules.admin_audit as admin_audit_module
    import app.database.repository_modules.errors as errors_module
    import app.database.repository_modules.favorites as favorites_module
    import app.database.repository_modules.search_cache as search_cache_module
    import app.database.repository_modules.searches as searches_module
    import app.database.repository_modules.spotify as spotify_module
    import app.database.repository_modules.tracks as tracks_module
    import app.database.repository_modules.users as users_module
    import app.health as health_module

    pool = await asyncpg.create_pool(pg_schema, min_size=1, max_size=3)

    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE users, tracks, errors, schema_migrations, search_cache, admin_audit RESTART IDENTITY CASCADE"
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
    monkeypatch.setattr(search_cache_module, "get_pool", _get_pool)
    monkeypatch.setattr(admin_audit_module, "get_pool", _get_pool)

    yield pool

    await pool.close()


@pytest_asyncio.fixture
async def live_redis(monkeypatch):
    """
    Function-scoped Redis client against the test-redis compose service.
    Requires REDIS_URL env var (default: redis://localhost:6380).
    Flushes the DB before and after each test for isolation.
    Patches redis_client._client so all rate-limit and trending-cache code
    uses this client instead of the production singleton.
    """
    import app.services.redis_client as redis_client_module

    url = os.environ.get("REDIS_URL", "redis://localhost:6380")
    client = aioredis.from_url(url, decode_responses=True)
    await client.ping()
    await client.flushdb()

    monkeypatch.setattr(redis_client_module, "_client", client)

    yield client

    await client.flushdb()
    await client.aclose()
