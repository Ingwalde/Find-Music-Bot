"""
Covers the None-narrowing guards added after mypy was run over the whole
package for the first time.

The headline case is real: Telegram omits CallbackQuery.message once the
message carrying the button is older than ~48h, so every callback that read
call.message.chat crashed with AttributeError for a user tapping a button on
last week's track card.
"""

import pytest

import app.bot.callbacks as callbacks
import app.bot.handlers as handlers
from app.bot.constants import CB_FAVORITE, CB_HISTORY, CB_LYRICS, CB_TRACK
from app.bot.keyboard_favorites import favorites_keyboard
from app.bot.keyboard_history import history_keyboard
from app.bot.keyboard_search import search_results_keyboard
from app.bot.keyboard_track import track_actions_keyboard
from app.localization.languages import DEFAULT_LANGUAGE
from tests.conftest import AsyncFakeBot, fake_call, fake_message, to_async

# ── callback_router: the 48h-old message case ────────────────────────────────


@pytest.mark.asyncio
async def test_router_tells_the_user_when_the_message_is_too_old(monkeypatch):
    """This is the crash that used to happen instead."""
    bot = AsyncFakeBot()
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))

    call = fake_call(data="track:123", user_id=1)
    call.message = None

    await callbacks.callback_router(call, bot)

    assert bot.answers, "the user must be told, not left with a dead button"
    _args, kwargs = bot.answers[-1]
    assert kwargs.get("show_alert") is True


@pytest.mark.asyncio
async def test_router_does_not_dispatch_when_the_message_is_too_old(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))

    dispatched = {"called": False}

    async def should_not_run(*args, **kwargs):
        dispatched["called"] = True

    monkeypatch.setattr(callbacks, "handle_track_callback", should_not_run)

    call = fake_call(data="track:123", user_id=1)
    call.message = None

    await callbacks.callback_router(call, bot)

    assert dispatched["called"] is False


@pytest.mark.asyncio
async def test_router_answers_and_stops_without_a_from_user(monkeypatch):
    bot = AsyncFakeBot()
    call = fake_call(data="track:123", user_id=1)
    call.from_user = None

    await callbacks.callback_router(call, bot)

    assert bot.answers


# ── handlers: message-side narrowing ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_user_context_falls_back_to_the_default_language(monkeypatch):
    """No from_user means nothing to upsert and no stored preference."""
    upserted = {"called": False}
    monkeypatch.setattr(
        handlers, "upsert_user", to_async(lambda user: upserted.update(called=True))
    )

    message = fake_message(user_id=1)
    message.from_user = None

    assert await handlers.get_user_context(message) == DEFAULT_LANGUAGE
    assert upserted["called"] is False


@pytest.mark.asyncio
async def test_require_admin_denies_when_there_is_no_user():
    """Absent identity must deny, never fall through to the admin path."""
    bot = AsyncFakeBot()
    message = fake_message(user_id=1)
    message.from_user = None

    assert await handlers.require_admin(bot, message, "en", "cmd_stats") is False


# ── keyboards: no dead buttons ───────────────────────────────────────────────


def test_search_keyboard_skips_tracks_without_an_id():
    markup = search_results_keyboard(
        tracks=[
            {"deezer_track_id": "1", "title": "Good", "artist": "A"},
            {"title": "No id", "artist": "B"},
        ],
        page=0,
        total_pages=1,
    )

    callbacks_rendered = [
        b.callback_data for row in markup.inline_keyboard for b in row
    ]
    assert f"{CB_TRACK}:1" in callbacks_rendered
    assert f"{CB_TRACK}:None" not in callbacks_rendered


def test_favorites_keyboard_skips_tracks_without_an_id():
    markup = favorites_keyboard(
        tracks=[
            {"deezer_track_id": "1", "title": "Good", "artist": "A"},
            {"title": "No id", "artist": "B"},
        ],
        language="en",
    )

    rendered = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert f"{CB_TRACK}:None" not in rendered


def test_history_keyboard_skips_entries_without_an_id():
    markup = history_keyboard(
        history=[{"id": 5, "query": "abba"}, {"query": "no id"}],
        language="en",
    )

    rendered = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert f"{CB_HISTORY}:5" in rendered
    assert f"{CB_HISTORY}:None" not in rendered


def test_track_keyboard_omits_track_buttons_without_an_id():
    """Lyrics and favourite used to render as ':None' while Similar guarded."""
    markup = track_actions_keyboard(
        {"title": "No id", "artist": "A"}, is_favorite=False, language="en"
    )

    rendered = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert not any(c and c.endswith(":None") for c in rendered)


def test_track_keyboard_renders_track_buttons_when_the_id_is_present():
    markup = track_actions_keyboard(
        {"deezer_track_id": "42", "title": "T", "artist": "A"},
        is_favorite=False,
        language="en",
    )

    rendered = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert f"{CB_LYRICS}:42" in rendered
    assert f"{CB_FAVORITE}:42" in rendered


# ── unbounded growth: favourites cap and long-message splitting ──────────────


@pytest.mark.asyncio
async def test_send_long_message_splits_past_the_telegram_limit():
    """
    split_long_message existed and was tested from day one but was never
    called from production code, so an over-length report hit the API limit.
    """
    from app.bot.actions import send_long_message

    bot = AsyncFakeBot()
    await send_long_message(bot, chat_id=1, text="x" * 9000)

    assert len(bot.messages) > 1
    assert "".join(args[1] for args, _ in bot.messages) == "x" * 9000


@pytest.mark.asyncio
async def test_send_long_message_sends_short_text_once():
    from app.bot.actions import send_long_message

    bot = AsyncFakeBot()
    await send_long_message(bot, chat_id=1, text="short")

    assert len(bot.messages) == 1


def test_favorites_limit_has_a_default():
    """The /favorites keyboard had no cap at all before this."""
    from app.config.settings import settings

    assert settings.FAVORITES_LIMIT > 0
