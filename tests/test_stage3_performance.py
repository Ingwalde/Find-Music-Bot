"""Covers the v3.7.10 Stage 3 changes: language plumbing, menu index, single-flight."""

import asyncio
import json

import pytest

import app.bot.callbacks as callbacks
import app.localization.translator as translator
import app.services.recommendations_service as recommendations
import app.services.redis_client as redis_client_module
from app.localization.translator import (
    MENU_ACTIONS,
    TRANSLATIONS,
    get_menu_action_by_text,
    t,
)
from tests.conftest import AsyncFakeBot, fake_call, to_async

# Captured at import, before conftest's autouse mock_retry_sleep fixture runs.
# That fixture patches http_retry_module.asyncio.sleep — but asyncio is a single
# shared module object, so it silently replaces asyncio.sleep *globally* with a
# no-op that never yields to the event loop. A concurrency test using the
# patched sleep runs its coroutines to completion one after another and passes
# no matter what the locking does: the first version of the single-flight test
# below asserted "one fetch" and passed against the broken implementation that
# actually fetched ten times.
_REAL_SLEEP = asyncio.sleep

# ── item 3: the router resolves language once, delegates receive it ──────────


@pytest.mark.asyncio
async def test_router_looks_language_up_exactly_once(monkeypatch):
    """Each button press used to issue two identical SELECTs."""
    bot = AsyncFakeBot()
    lookups: list[int] = []

    monkeypatch.setattr(
        callbacks,
        "get_user_language",
        to_async(lambda user_id: lookups.append(user_id) or "en"),
    )
    monkeypatch.setattr(callbacks, "handle_track_callback", to_async(lambda *a: None))

    await callbacks.callback_router(fake_call(data="track:1", user_id=42), bot)

    assert lookups == [42]


@pytest.mark.asyncio
async def test_delegate_receives_the_callers_own_language(monkeypatch):
    """
    The failure this guards against: passing some *other* user's language.
    Handler tests mock get_user_language, so they would not notice — this
    resolves two distinct users and checks each gets their own value.
    """
    bot = AsyncFakeBot()
    languages = {7: "uk", 8: "de"}
    received: list[tuple[int, str]] = []

    monkeypatch.setattr(
        callbacks, "get_user_language", to_async(lambda user_id: languages[user_id])
    )

    async def spy(bot_, call_, track_id, language):
        received.append((call_.from_user.id, language))

    monkeypatch.setattr(callbacks, "handle_track_callback", spy)

    await callbacks.callback_router(fake_call(data="track:1", user_id=7), bot)
    await callbacks.callback_router(fake_call(data="track:1", user_id=8), bot)

    assert received == [(7, "uk"), (8, "de")]


@pytest.mark.asyncio
async def test_every_delegate_takes_a_language_parameter():
    """A delegate that still resolved it itself would reintroduce the second query."""
    import inspect

    import app.bot.favorites_callbacks as fav
    import app.bot.history_callbacks as hist
    import app.bot.language_callbacks as lang
    import app.bot.lyrics_callbacks as lyr
    import app.bot.pagination_callbacks as pag
    import app.bot.similar_callbacks as sim
    import app.bot.track_callbacks as trk

    for module in (fav, hist, lang, lyr, pag, sim, trk):
        handlers = [
            (n, o) for n, o in vars(module).items()
            if n.startswith("handle_") and inspect.iscoroutinefunction(o)
        ]
        assert handlers, f"{module.__name__} exposes no handlers"

        for name, fn in handlers:
            params = inspect.signature(fn).parameters
            assert "language" in params, f"{module.__name__}.{name} lost the parameter"


# ── item 4: precomputed menu index must match the old nested loop ────────────


def _old_lookup(text: str) -> str | None:
    """The implementation the index replaced, kept here as the oracle."""
    normalized = text.strip().lower()
    for language in TRANSLATIONS:
        for key, action in MENU_ACTIONS.items():
            if normalized == t(key, language).lower():
                return action
    return None


def test_menu_index_matches_the_previous_implementation_for_every_button():
    """Exhaustive over every button text in every language."""
    for language in TRANSLATIONS:
        for key in MENU_ACTIONS:
            text = t(key, language)
            assert get_menu_action_by_text(text) == _old_lookup(text), (
                f"diverged on {text!r} ({language}/{key})"
            )


@pytest.mark.parametrize(
    "text", ["", "   ", "abba", "Bohemian Rhapsody", "/start", "музика ще щось"]
)
def test_menu_index_matches_for_non_matching_text(text):
    assert get_menu_action_by_text(text) == _old_lookup(text)


def test_menu_index_is_case_and_whitespace_insensitive():
    text = t("btn_favorites", "en")

    assert get_menu_action_by_text(f"  {text.upper()}  ") == "favorites"


def test_menu_index_resolves_collisions_first_binding_wins():
    """
    Distinct locales share some button texts, so the index is smaller than
    languages x actions. setdefault must keep the first binding, matching the
    old loop's first-match-wins order.
    """
    assert len(translator.MENU_ACTION_INDEX) < len(TRANSLATIONS) * len(MENU_ACTIONS)

    rebuilt = translator._build_menu_action_index()
    assert rebuilt == translator.MENU_ACTION_INDEX, "index build is not deterministic"


# ── item 7: single-flight and both cache tiers ──────────────────────────────


@pytest.fixture
def fresh_trending_lock(monkeypatch):
    """
    Gives each test its own lock.

    _trending_cache_lock is created at module import, outside any event loop,
    and asyncio.Lock binds to the loop on first use. Production has a single
    loop for the process lifetime so that is fine, but pytest-asyncio creates a
    new loop per test — once a test holds the lock across an await, the next
    test inherits a lock bound to (and left locked by) a dead loop and fails
    with "bound to a different event loop".
    """
    monkeypatch.setattr(recommendations, "_trending_cache_lock", asyncio.Lock())
    recommendations.invalidate_trending_cache()


@pytest.mark.asyncio
async def test_concurrent_cold_reads_fetch_only_once(monkeypatch, fresh_trending_lock):
    """
    The lock used to be released before the fetch, so N concurrent /trending
    calls on a cold cache all reached Deezer.
    """
    monkeypatch.setattr(redis_client_module, "_client", None)
    recommendations.invalidate_trending_cache()

    calls = {"n": 0}

    async def slow_fetch(limit):
        calls["n"] += 1
        await _REAL_SLEEP(0.05)
        return [{"deezer_track_id": "1"}]

    await asyncio.gather(
        *(recommendations.get_cached_trending(slow_fetch, limit=1) for _ in range(10))
    )

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_queued_callers_get_the_winners_result(monkeypatch, fresh_trending_lock):
    monkeypatch.setattr(redis_client_module, "_client", None)
    recommendations.invalidate_trending_cache()

    async def fetch(limit):
        await _REAL_SLEEP(0.02)
        return [{"deezer_track_id": "42"}]

    results = await asyncio.gather(
        *(recommendations.get_cached_trending(fetch, limit=1) for _ in range(5))
    )

    assert all(r == [{"deezer_track_id": "42"}] for r in results)


@pytest.mark.asyncio
async def test_in_memory_tier_is_filled_even_when_redis_succeeds(monkeypatch, fresh_trending_lock):
    """
    The early return after a successful Redis write left the in-memory tier
    permanently cold, so the fallback was empty the moment Redis went away.
    """
    store: dict[str, str] = {}

    class FakeRedis:
        async def get(self, key):
            return store.get(key)

        async def set(self, key, value, ex=None):
            store[key] = value

    monkeypatch.setattr(redis_client_module, "_client", FakeRedis())
    recommendations.invalidate_trending_cache()

    tracks = [{"deezer_track_id": "7"}]
    await recommendations.get_cached_trending(to_async(lambda limit: tracks), limit=1)

    assert store, "Redis tier was not written"
    assert recommendations._trending_cache["tracks"] == tracks, (
        "in-memory tier stayed cold — the fallback would be empty on a Redis outage"
    )


@pytest.mark.asyncio
async def test_fallback_serves_from_memory_after_redis_disappears(monkeypatch, fresh_trending_lock):
    """End to end for the above: warm with Redis up, then take Redis away."""
    store: dict[str, str] = {}

    class FakeRedis:
        async def get(self, key):
            return store.get(key)

        async def set(self, key, value, ex=None):
            store[key] = value

    monkeypatch.setattr(redis_client_module, "_client", FakeRedis())
    recommendations.invalidate_trending_cache()

    calls = {"n": 0}

    async def fetch(limit):
        calls["n"] += 1
        return [{"deezer_track_id": "9"}]

    await recommendations.get_cached_trending(fetch, limit=1)
    assert calls["n"] == 1

    monkeypatch.setattr(redis_client_module, "_client", None)
    result = await recommendations.get_cached_trending(fetch, limit=1)

    assert calls["n"] == 1, "Redis outage forced a refetch — fallback was cold"
    assert result == [{"deezer_track_id": "9"}]


@pytest.mark.asyncio
async def test_redis_hit_still_short_circuits(monkeypatch, fresh_trending_lock):
    """The fast path must survive the restructuring."""
    tracks = [{"deezer_track_id": "cached"}]

    class FakeRedis:
        async def get(self, key):
            return json.dumps(tracks)

        async def set(self, key, value, ex=None):
            raise AssertionError("must not write on a hit")

    monkeypatch.setattr(redis_client_module, "_client", FakeRedis())
    recommendations.invalidate_trending_cache()

    called = {"n": 0}

    async def fetch(limit):
        called["n"] += 1
        return []

    assert await recommendations.get_cached_trending(fetch, limit=1) == tracks
    assert called["n"] == 0
