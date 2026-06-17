import pytest

from app.bot import handlers
from tests.conftest import AsyncFakeBot, fake_message, to_async


def make_track_dict(title="SOS", artist="ABBA"):
    return {
        "deezer_track_id": "1",
        "title": title,
        "artist": artist,
        "deezer_link": "https://deezer.com/track/1",
    }


def _setup_common(monkeypatch):
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))


# ── 7A: helpers ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_admin_delegates_to_is_admin_user(monkeypatch):
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: user_id == 123)

    assert await handlers.is_admin(123) is True
    assert await handlers.is_admin(999) is False


@pytest.mark.asyncio
async def test_format_recent_errors_handles_empty_and_items(monkeypatch):
    monkeypatch.setattr(handlers, "get_recent_errors", to_async(lambda limit: []))
    result = await handlers.format_recent_errors("en")
    assert result

    monkeypatch.setattr(
        handlers,
        "get_recent_errors",
        to_async(lambda limit: [{"source": "unit", "created_at": "today", "error_message": "boom", "telegram_id": 123}]),
    )
    formatted = await handlers.format_recent_errors("en")

    assert "unit" in formatted
    assert "boom" in formatted
    assert "123" in formatted


# ── 7B: simple user commands ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_show_language_menu(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)

    await handlers.show_language_menu(bot, fake_message())

    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_show_favorites_empty_and_with_tracks(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)

    monkeypatch.setattr(handlers, "get_favorite_tracks", to_async(lambda user_id: []))
    await handlers.show_favorites(bot, fake_message())

    monkeypatch.setattr(handlers, "get_favorite_tracks", to_async(lambda user_id: [sample_track]))
    await handlers.show_favorites(bot, fake_message())

    assert len(bot.messages) >= 4
    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_show_favorites_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(
        handlers, "upsert_user", lambda user: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "log_and_save_error", to_async(lambda **kwargs: None))

    await handlers.show_favorites(bot, fake_message())

    assert bot.messages


@pytest.mark.asyncio
async def test_show_history_empty_and_with_items(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)

    monkeypatch.setattr(handlers, "get_search_history", to_async(lambda user_id, limit: []))
    await handlers.show_history(bot, fake_message())

    monkeypatch.setattr(
        handlers,
        "get_search_history",
        to_async(lambda user_id, limit: [{"id": 1, "query": "SOS"}]),
    )
    await handlers.show_history(bot, fake_message())

    assert len(bot.messages) >= 4
    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_show_history_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(
        handlers, "upsert_user", lambda user: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "log_and_save_error", to_async(lambda **kwargs: None))

    await handlers.show_history(bot, fake_message())

    assert bot.messages


@pytest.mark.asyncio
async def test_command_handlers(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: user_id == 123)
    monkeypatch.setattr(handlers, "format_recent_errors", to_async(lambda language="en": "errors"))
    monkeypatch.setattr(handlers, "format_health_report", to_async(lambda: "health"))
    monkeypatch.setattr(handlers, "clear_errors", to_async(lambda: None))
    monkeypatch.setattr(
        handlers,
        "show_favorites",
        to_async(lambda b, m: b.messages.append(((m.chat.id, "favorites"), {}))),
    )
    monkeypatch.setattr(
        handlers,
        "show_history",
        to_async(lambda b, m: b.messages.append(((m.chat.id, "history"), {}))),
    )
    monkeypatch.setattr(
        handlers,
        "show_language_menu",
        to_async(lambda b, m: b.messages.append(((m.chat.id, "language"), {}))),
    )

    msg = fake_message()
    admin_msg = fake_message(user_id=123)

    await handlers.start_handler(msg, bot)
    await handlers.help_handler(msg, bot)
    await handlers.language_handler(msg, bot)
    await handlers.version_handler(msg, bot)
    await handlers.errors_handler(admin_msg, bot)
    await handlers.clear_errors_handler(admin_msg, bot)
    await handlers.health_handler(admin_msg, bot)
    await handlers.favorites_handler(msg, bot)
    await handlers.history_handler(msg, bot)

    assert len(bot.messages) >= 9


# ── process_music_search ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_music_search_rejects_non_text(monkeypatch):
    bot = AsyncFakeBot()
    called = {}
    _setup_common(monkeypatch)
    monkeypatch.setattr(
        handlers,
        "ask_for_music",
        to_async(lambda bot, chat_id, user_id: called.update(asked=True)),
    )

    await handlers.process_music_search(bot, fake_message(text=None))

    assert called["asked"] is True


@pytest.mark.asyncio
async def test_process_music_search_handles_commands_and_regular_query(monkeypatch):
    bot = AsyncFakeBot()
    called = {}
    _setup_common(monkeypatch)
    monkeypatch.setattr(
        handlers, "send_search_results", to_async(lambda **kwargs: called.update(kwargs))
    )

    await handlers.process_music_search(bot, fake_message(text="/start"))

    assert bot.messages == []
    assert called == {}

    await handlers.process_music_search(bot, fake_message(text="SOS"))

    assert called["query"] == "SOS"


@pytest.mark.asyncio
async def test_process_music_search_handles_search_error(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(
        handlers,
        "send_search_results",
        to_async(lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))),
    )
    monkeypatch.setattr(handlers, "log_and_save_error", to_async(lambda **kwargs: None))

    await handlers.process_music_search(bot, fake_message(text="SOS"))

    assert bot.messages


# ── 7C: admin commands ────────────────────────────────────────────────────────


# (full admin handler coverage is in test_admin_handlers.py)


# ── 7D: similar_handler ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_similar_handler_sends_no_context_message_when_no_last_track(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "get_last_track_id", to_async(lambda uid: None))

    await handlers.similar_handler(fake_message(), bot)

    assert bot.messages
    assert (
        "Open" in bot.messages[-1][0][1]
        or "Відкрий" in bot.messages[-1][0][1]
        or "similar" in bot.messages[-1][0][1].lower()
    )


@pytest.mark.asyncio
async def test_similar_handler_sends_tracks_when_context_exists(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "get_last_track_id", to_async(lambda uid: "42"))
    monkeypatch.setattr(handlers, "deezer_get_track", to_async(lambda tid: make_track_dict()))
    monkeypatch.setattr(
        handlers,
        "get_similar_by_genre",
        to_async(lambda tid, artist_name="": [make_track_dict("Waterloo")]),
    )

    await handlers.similar_handler(fake_message(), bot)

    assert bot.messages
    assert "Waterloo" in bot.messages[-1][0][1]


@pytest.mark.asyncio
async def test_similar_handler_sends_empty_message_when_no_similar_tracks(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "get_last_track_id", to_async(lambda uid: "42"))
    monkeypatch.setattr(handlers, "deezer_get_track", to_async(lambda tid: make_track_dict()))
    monkeypatch.setattr(
        handlers, "get_similar_by_genre", to_async(lambda tid, artist_name="": [])
    )

    await handlers.similar_handler(fake_message(), bot)

    assert bot.messages
    assert "No similar" in bot.messages[-1][0][1]


@pytest.mark.asyncio
async def test_similar_handler_handles_exception(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "get_last_track_id", to_async(lambda uid: "42"))
    monkeypatch.setattr(handlers, "deezer_get_track", to_async(lambda tid: make_track_dict()))
    monkeypatch.setattr(
        handlers,
        "get_similar_by_genre",
        to_async(lambda tid, artist_name="": (_ for _ in ()).throw(RuntimeError("fail"))),
    )
    monkeypatch.setattr(handlers, "log_and_save_error", to_async(lambda **kwargs: None))

    await handlers.similar_handler(fake_message(), bot)

    assert bot.messages


# ── 7D: trending_handler ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_handler_sends_tracks(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    tracks = [make_track_dict(f"Track {i}") for i in range(3)]
    monkeypatch.setattr(handlers, "get_cached_trending", to_async(lambda fetch_fn: tracks))

    await handlers.trending_handler(fake_message(), bot)

    assert bot.messages
    text = bot.messages[-1][0][1]
    assert "Track 0" in text


@pytest.mark.asyncio
async def test_trending_handler_sends_empty_message_when_no_tracks(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(handlers, "get_cached_trending", to_async(lambda fetch_fn: []))

    await handlers.trending_handler(fake_message(), bot)

    assert bot.messages
    assert "not available" in bot.messages[-1][0][1]


@pytest.mark.asyncio
async def test_trending_handler_handles_exception(monkeypatch):
    bot = AsyncFakeBot()
    _setup_common(monkeypatch)
    monkeypatch.setattr(
        handlers,
        "get_cached_trending",
        to_async(lambda fetch_fn: (_ for _ in ()).throw(RuntimeError("api down"))),
    )
    monkeypatch.setattr(handlers, "log_and_save_error", to_async(lambda **kwargs: None))

    await handlers.trending_handler(fake_message(), bot)

    assert bot.messages


# ── 7E: text_handler routing ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_text_handler_routes_actions(monkeypatch):
    bot = AsyncFakeBot()
    routed = []
    action_seq = iter(["main_menu", "music", "favorites", "history", "language", None])
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: next(action_seq))
    monkeypatch.setattr(
        handlers, "show_main_menu", to_async(lambda bot, chat_id, user_id: routed.append("main"))
    )
    monkeypatch.setattr(
        handlers, "ask_for_music", to_async(lambda bot, chat_id, user_id: routed.append("music"))
    )
    # async handlers in handlers.py — need to_async
    monkeypatch.setattr(
        handlers, "show_favorites", to_async(lambda bot, message: routed.append("favorites"))
    )
    monkeypatch.setattr(
        handlers, "show_history", to_async(lambda bot, message: routed.append("history"))
    )
    monkeypatch.setattr(
        handlers, "show_language_menu", to_async(lambda bot, message: routed.append("language"))
    )
    monkeypatch.setattr(
        handlers, "process_music_search", to_async(lambda bot, message: routed.append("search"))
    )

    for _ in range(6):
        await handlers.text_handler(fake_message(), bot)

    assert routed == ["main", "music", "favorites", "history", "language", "search"]
