import pytest

from app.bot import (
    callbacks,
    favorites_callbacks,
    history_callbacks,
    language_callbacks,
    lyrics_callbacks,
    pagination_callbacks,
    track_callbacks,
)
from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_FAVORITES_CLEAR_CANCEL,
    ACTION_FAVORITES_CLEAR_CONFIRM,
    ACTION_FAVORITES_CLEAR_REQUEST,
    ACTION_HISTORY_CLEAR_CANCEL,
    ACTION_HISTORY_CLEAR_CONFIRM,
    ACTION_HISTORY_CLEAR_REQUEST,
    ACTION_MAIN_MENU,
    ACTION_NOOP,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_HISTORY,
    CB_LANGUAGE,
    CB_LYRICS,
    CB_PAGE,
    CB_TRACK,
    CB_UNFAVORITE,
)
from app.bot.context import save_search_context
from tests.conftest import AsyncFakeBot, fake_call, to_async


@pytest.mark.asyncio
async def test_language_callback_rejects_unsupported_language(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(language_callbacks, "is_supported_language", lambda code: False)

    await language_callbacks.handle_language_callback(bot, fake_call(), "xx")

    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_language_callback_saves_supported_language(monkeypatch):
    bot = AsyncFakeBot()
    saved = {}
    monkeypatch.setattr(language_callbacks, "is_supported_language", lambda code: True)
    monkeypatch.setattr(language_callbacks, "upsert_user", to_async(lambda user: saved.update(user=user.id)))
    monkeypatch.setattr(language_callbacks, "set_user_language", to_async(lambda user_id, code: saved.update(language=code)))

    await language_callbacks.handle_language_callback(bot, fake_call(), "uk")

    assert saved == {"user": 123, "language": "uk"}
    assert bot.messages


@pytest.mark.asyncio
async def test_language_callback_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(language_callbacks, "is_supported_language", lambda code: True)
    monkeypatch.setattr(
        language_callbacks,
        "upsert_user",
        lambda user: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(language_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await language_callbacks.handle_language_callback(bot, fake_call(), "uk")

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_track_cache_loader_uses_cache(monkeypatch, sample_track):
    monkeypatch.setattr(track_callbacks, "get_track_by_deezer_id", to_async(lambda track_id: sample_track))

    assert await track_callbacks.get_track_from_cache_or_deezer("671298") == sample_track


@pytest.mark.asyncio
async def test_track_cache_loader_falls_back_to_deezer(monkeypatch, sample_track):
    saved = {}
    monkeypatch.setattr(track_callbacks, "get_track_by_deezer_id", to_async(lambda track_id: None))
    monkeypatch.setattr(track_callbacks, "get_track", to_async(lambda track_id: sample_track))
    monkeypatch.setattr(track_callbacks, "save_track", to_async(lambda track: saved.update(track=track)))

    assert await track_callbacks.get_track_from_cache_or_deezer("671298") == sample_track
    assert saved["track"] == sample_track


@pytest.mark.asyncio
async def test_track_callback_sends_track_card(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    called = {}
    monkeypatch.setattr(track_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(track_callbacks, "get_track_from_cache_or_deezer", to_async(lambda track_id: sample_track))
    monkeypatch.setattr(track_callbacks, "send_track_card", to_async(lambda **kwargs: called.update(kwargs)))

    await track_callbacks.handle_track_callback(bot, fake_call(), "671298")

    assert bot.answers
    assert called["track"] == sample_track


@pytest.mark.asyncio
async def test_track_callback_handles_error(monkeypatch):
    bot = AsyncFakeBot()

    async def failing_loader(track_id):
        raise RuntimeError("fail")

    monkeypatch.setattr(track_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(track_callbacks, "get_track_from_cache_or_deezer", failing_loader)
    monkeypatch.setattr(track_callbacks, "log_and_save_error", to_async(lambda *args, **kwargs: None))

    await track_callbacks.handle_track_callback(bot, fake_call(), "bad")

    assert bot.messages


@pytest.mark.asyncio
async def test_lyrics_callback_sends_genius_link(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(lyrics_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(lyrics_callbacks, "get_track", to_async(lambda track_id: {"title": "SOS", "artist": "ABBA"}))
    monkeypatch.setattr(lyrics_callbacks, "find_lyrics_url", to_async(lambda title, artist: "https://genius.com/abba-sos"))

    await lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.answers
    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_lyrics_callback_handles_missing_lyrics(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(lyrics_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(lyrics_callbacks, "get_track", to_async(lambda track_id: {"title": "Unknown", "artist": "Unknown"}))
    monkeypatch.setattr(lyrics_callbacks, "find_lyrics_url", to_async(lambda title, artist: None))

    await lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.messages


@pytest.mark.asyncio
async def test_lyrics_callback_handles_get_track_error(monkeypatch):
    bot = AsyncFakeBot()

    async def failing_get_track(track_id):
        raise RuntimeError("api down")

    monkeypatch.setattr(lyrics_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(lyrics_callbacks, "get_track", failing_get_track)
    monkeypatch.setattr(lyrics_callbacks, "log_and_save_error", to_async(lambda *args, **kwargs: None))

    await lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.answers
    assert len(bot.messages) == 1


# ── pagination callbacks ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_page_callback_handles_expired_context(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(pagination_callbacks, "get_user_language", to_async(lambda user_id: "en"))

    await pagination_callbacks.handle_page_callback(bot, fake_call(), 1)

    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_page_callback_edits_current_page(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(pagination_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    await save_search_context(123, "SOS", [sample_track, sample_track | {"deezer_track_id": "2"}])

    await pagination_callbacks.handle_page_callback(bot, fake_call(), 0)

    assert bot.edited_texts
    assert bot.answers


@pytest.mark.asyncio
async def test_back_to_results_callback_calls_action(monkeypatch):
    bot = AsyncFakeBot()
    called = {}
    monkeypatch.setattr(pagination_callbacks, "get_user_language", to_async(lambda user_id: "en"))

    import app.bot.actions as action_module

    monkeypatch.setattr(
        action_module,
        "send_current_results_page",
        to_async(lambda **kwargs: called.update(kwargs)),
    )

    await pagination_callbacks.handle_back_to_results_callback(bot, fake_call())

    assert called["user_id"] == 123


# ── favorites callbacks ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_favorite_callback_success(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(favorites_callbacks, "get_track", to_async(lambda track_id: sample_track))
    monkeypatch.setattr(favorites_callbacks, "save_track", to_async(lambda track: None))
    monkeypatch.setattr(favorites_callbacks, "add_favorite", to_async(lambda user_id, track: None))
    monkeypatch.setattr(
        favorites_callbacks, "user_has_search_context", to_async(lambda user_id: False)
    )

    await favorites_callbacks.handle_favorite_callback(bot, fake_call(), "671298")

    assert bot.edited_markups
    assert bot.answers


@pytest.mark.asyncio
async def test_remove_favorite_callback_success(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "get_track", to_async(lambda track_id: sample_track))
    monkeypatch.setattr(favorites_callbacks, "save_track", to_async(lambda track: None))
    monkeypatch.setattr(favorites_callbacks, "remove_favorite", to_async(lambda **kwargs: None))
    monkeypatch.setattr(
        favorites_callbacks, "user_has_search_context", to_async(lambda user_id: True)
    )

    await favorites_callbacks.handle_remove_favorite_callback(bot, fake_call(), "671298")

    assert bot.edited_markups


@pytest.mark.asyncio
async def test_clear_favorites_request_and_confirm(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "clear_favorites", to_async(lambda user_id: None))

    await favorites_callbacks.handle_clear_favorites_request_callback(bot, fake_call())
    await favorites_callbacks.handle_clear_favorites_confirm_callback(bot, fake_call())

    assert len(bot.edited_texts) == 2


@pytest.mark.asyncio
async def test_clear_favorites_cancel_handles_empty_and_non_empty(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "get_favorite_tracks", to_async(lambda user_id: []))
    await favorites_callbacks.handle_clear_favorites_cancel_callback(bot, fake_call())

    monkeypatch.setattr(favorites_callbacks, "get_favorite_tracks", to_async(lambda user_id: [sample_track]))
    await favorites_callbacks.handle_clear_favorites_cancel_callback(bot, fake_call())

    assert len(bot.edited_texts) == 2


@pytest.mark.asyncio
async def test_favorite_callback_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(
        favorites_callbacks,
        "get_track",
        to_async(lambda track_id: (_ for _ in ()).throw(RuntimeError("deezer down"))),
    )
    monkeypatch.setattr(favorites_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await favorites_callbacks.handle_favorite_callback(bot, fake_call(), "671298")

    assert calls
    assert bot.answers[-1][0][1] == "Could not add to favorites."
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_remove_favorite_callback_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        favorites_callbacks,
        "get_track",
        to_async(lambda track_id: (_ for _ in ()).throw(RuntimeError("deezer down"))),
    )
    monkeypatch.setattr(favorites_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await favorites_callbacks.handle_remove_favorite_callback(bot, fake_call(), "671298")

    assert calls
    assert bot.answers[-1][0][1] == "Could not remove from favorites."
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_clear_favorites_request_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    bot.raise_on_edit = True
    calls = []
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(favorites_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await favorites_callbacks.handle_clear_favorites_request_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_clear_favorites_confirm_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        favorites_callbacks,
        "clear_favorites",
        lambda user_id: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(favorites_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await favorites_callbacks.handle_clear_favorites_confirm_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_clear_favorites_cancel_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(favorites_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        favorites_callbacks,
        "get_favorite_tracks",
        lambda user_id: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(favorites_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await favorites_callbacks.handle_clear_favorites_cancel_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


# ── history callbacks ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_history_search_callback_not_found(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(history_callbacks, "get_search_query_by_id", to_async(lambda **kwargs: None))

    await history_callbacks.handle_history_search_callback(bot, fake_call(), "99")

    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_history_search_callback_repeats_query(monkeypatch):
    bot = AsyncFakeBot()
    called = {}
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(history_callbacks, "get_search_query_by_id", to_async(lambda **kwargs: "SOS"))
    monkeypatch.setattr(history_callbacks, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(
        history_callbacks, "send_search_results", to_async(lambda **kwargs: called.update(kwargs))
    )

    await history_callbacks.handle_history_search_callback(bot, fake_call(), "1")

    assert called["query"] == "SOS"


@pytest.mark.asyncio
async def test_clear_history_request_confirm_and_cancel(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(history_callbacks, "clear_search_history", to_async(lambda user_id: None))
    monkeypatch.setattr(history_callbacks, "get_search_history", to_async(lambda user_id, limit: []))

    await history_callbacks.handle_clear_history_request_callback(bot, fake_call())
    await history_callbacks.handle_clear_history_confirm_callback(bot, fake_call())
    await history_callbacks.handle_clear_history_cancel_callback(bot, fake_call())

    assert len(bot.edited_texts) == 3


@pytest.mark.asyncio
async def test_history_search_callback_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        history_callbacks,
        "get_search_query_by_id",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(history_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await history_callbacks.handle_history_search_callback(bot, fake_call(), "1")

    assert calls
    assert bot.messages[-1][0][1] == "Could not repeat this search."


@pytest.mark.asyncio
async def test_clear_history_request_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    bot.raise_on_edit = True
    calls = []
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(history_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await history_callbacks.handle_clear_history_request_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_clear_history_confirm_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        history_callbacks,
        "clear_search_history",
        lambda user_id: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(history_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await history_callbacks.handle_clear_history_confirm_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


@pytest.mark.asyncio
async def test_clear_history_cancel_shows_history_when_not_empty(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        history_callbacks,
        "get_search_history",
        to_async(lambda user_id, limit: [{"id": 1, "query": "SOS"}]),
    )

    await history_callbacks.handle_clear_history_cancel_callback(bot, fake_call())

    assert bot.edited_texts
    assert bot.edited_texts[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_clear_history_cancel_handles_error(monkeypatch):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(history_callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        history_callbacks,
        "get_search_history",
        lambda user_id, limit: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(history_callbacks, "log_and_save_error", to_async(lambda *a, **k: calls.append(1)))

    await history_callbacks.handle_clear_history_cancel_callback(bot, fake_call())

    assert calls
    assert bot.answers[-1][1]["show_alert"] is True


# ── callback router ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_callback_router_routes_main_actions(monkeypatch):
    bot = AsyncFakeBot()
    called = []
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        callbacks,
        "show_main_menu",
        to_async(lambda bot, chat_id, user_id: called.append(("main", user_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "ask_for_music",
        to_async(lambda bot, chat_id, user_id: called.append(("search", user_id))),
    )

    await callbacks.callback_router(fake_call(ACTION_MAIN_MENU), bot)
    await callbacks.callback_router(fake_call(ACTION_SEARCH_AGAIN), bot)
    await callbacks.callback_router(fake_call(ACTION_NOOP), bot)
    await callbacks.callback_router(fake_call("unknown"), bot)

    assert ("main", 123) in called
    assert ("search", 123) in called
    assert len(bot.answers) >= 4


@pytest.mark.asyncio
async def test_callback_router_routes_prefixed_actions(monkeypatch):
    bot = AsyncFakeBot()
    routed = []
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(
        callbacks,
        "handle_language_callback",
        to_async(lambda bot, call, language_code: routed.append((CB_LANGUAGE, language_code))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_track_callback",
        to_async(lambda bot, call, track_id: routed.append((CB_TRACK, track_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_page_callback",
        to_async(lambda bot, call, page: routed.append((CB_PAGE, page))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_back_to_results_callback",
        to_async(lambda bot, call: routed.append((ACTION_BACK_RESULTS, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_favorite_callback",
        to_async(lambda bot, call, track_id: routed.append((CB_FAVORITE, track_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_remove_favorite_callback",
        to_async(lambda bot, call, track_id: routed.append((CB_UNFAVORITE, track_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_lyrics_callback",
        to_async(lambda bot, call, track_id: routed.append((CB_LYRICS, track_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_history_search_callback",
        to_async(lambda bot, call, search_id: routed.append((CB_HISTORY, search_id))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_favorites_request_callback",
        to_async(lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_REQUEST, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_favorites_confirm_callback",
        to_async(lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_CONFIRM, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_favorites_cancel_callback",
        to_async(lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_CANCEL, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_history_request_callback",
        to_async(lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_REQUEST, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_history_confirm_callback",
        to_async(lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_CONFIRM, None))),
    )
    monkeypatch.setattr(
        callbacks,
        "handle_clear_history_cancel_callback",
        to_async(lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_CANCEL, None))),
    )

    for data in [
        f"{CB_LANGUAGE}:uk",
        f"{CB_TRACK}:1",
        f"{CB_PAGE}:2",
        ACTION_BACK_RESULTS,
        f"{CB_FAVORITE}:1",
        f"{CB_UNFAVORITE}:1",
        ACTION_FAVORITES_CLEAR_REQUEST,
        ACTION_FAVORITES_CLEAR_CONFIRM,
        ACTION_FAVORITES_CLEAR_CANCEL,
        f"{CB_LYRICS}:1",
        f"{CB_HISTORY}:7",
        ACTION_HISTORY_CLEAR_REQUEST,
        ACTION_HISTORY_CLEAR_CONFIRM,
        ACTION_HISTORY_CLEAR_CANCEL,
    ]:
        await callbacks.callback_router(fake_call(data), bot)

    assert (CB_LANGUAGE, "uk") in routed
    assert (CB_PAGE, 2) in routed
    assert (ACTION_HISTORY_CLEAR_CANCEL, None) in routed
