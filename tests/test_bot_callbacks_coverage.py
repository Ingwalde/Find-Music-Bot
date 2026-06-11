from types import SimpleNamespace

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


class FakeBot:
    def __init__(self):
        self.answers = []
        self.messages = []
        self.edited_texts = []
        self.edited_markups = []
        self.callback_handlers = []

    def answer_callback_query(self, *args, **kwargs):
        self.answers.append((args, kwargs))

    def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))

    def edit_message_text(self, *args, **kwargs):
        self.edited_texts.append((args, kwargs))

    def edit_message_reply_markup(self, *args, **kwargs):
        self.edited_markups.append((args, kwargs))

    def callback_query_handler(self, **decorator_kwargs):
        def decorator(func):
            self.callback_handlers.append((decorator_kwargs, func))
            return func

        return decorator


def fake_call(data="noop", user_id=123):
    return SimpleNamespace(
        id="call-id",
        data=data,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        message=SimpleNamespace(chat=SimpleNamespace(id=10), message_id=20),
    )


def test_language_callback_rejects_unsupported_language(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(language_callbacks, "is_supported_language", lambda code: False)

    language_callbacks.handle_language_callback(bot, fake_call(), "xx")

    assert bot.answers[-1][1]["show_alert"] is True


def test_language_callback_saves_supported_language(monkeypatch):
    bot = FakeBot()
    saved = {}
    monkeypatch.setattr(language_callbacks, "is_supported_language", lambda code: True)
    monkeypatch.setattr(language_callbacks, "upsert_user", lambda user: saved.update(user=user.id))
    monkeypatch.setattr(language_callbacks, "set_user_language", lambda user_id, code: saved.update(language=code))

    language_callbacks.handle_language_callback(bot, fake_call(), "uk")

    assert saved == {"user": 123, "language": "uk"}
    assert bot.messages


def test_track_cache_loader_uses_cache(monkeypatch, sample_track):
    monkeypatch.setattr(track_callbacks, "get_track_by_deezer_id", lambda track_id: sample_track)

    assert track_callbacks.get_track_from_cache_or_deezer("671298") == sample_track


def test_track_cache_loader_falls_back_to_deezer(monkeypatch, sample_track):
    saved = {}
    monkeypatch.setattr(track_callbacks, "get_track_by_deezer_id", lambda track_id: None)
    monkeypatch.setattr(track_callbacks, "get_track", lambda track_id: sample_track)
    monkeypatch.setattr(track_callbacks, "save_track", lambda track: saved.update(track=track))

    assert track_callbacks.get_track_from_cache_or_deezer("671298") == sample_track
    assert saved["track"] == sample_track


def test_track_callback_sends_track_card(monkeypatch, sample_track):
    bot = FakeBot()
    called = {}
    monkeypatch.setattr(track_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(track_callbacks, "get_track_from_cache_or_deezer", lambda track_id: sample_track)
    monkeypatch.setattr(track_callbacks, "send_track_card", lambda **kwargs: called.update(kwargs))

    track_callbacks.handle_track_callback(bot, fake_call(), "671298")

    assert bot.answers
    assert called["track"] == sample_track


def test_track_callback_handles_error(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(track_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(track_callbacks, "get_track_from_cache_or_deezer", lambda track_id: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(track_callbacks, "log_and_save_error", lambda *args, **kwargs: None)

    track_callbacks.handle_track_callback(bot, fake_call(), "bad")

    assert bot.messages


def test_lyrics_callback_sends_genius_link(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(lyrics_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(lyrics_callbacks, "get_track", lambda track_id: {"title": "SOS", "artist": "ABBA"})
    monkeypatch.setattr(lyrics_callbacks, "find_lyrics_url", lambda title, artist: "https://genius.com/abba-sos")

    lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.answers
    assert bot.messages[-1][1]["reply_markup"] is not None


def test_lyrics_callback_handles_missing_lyrics(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(lyrics_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(lyrics_callbacks, "get_track", lambda track_id: {"title": "Unknown", "artist": "Unknown"})
    monkeypatch.setattr(lyrics_callbacks, "find_lyrics_url", lambda title, artist: None)

    lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.messages


def test_lyrics_callback_handles_get_track_error(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(lyrics_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(lyrics_callbacks, "get_track", lambda track_id: (_ for _ in ()).throw(RuntimeError("api down")))
    monkeypatch.setattr(lyrics_callbacks, "log_and_save_error", lambda *args, **kwargs: None)

    lyrics_callbacks.handle_lyrics_callback(bot, fake_call(), "1")

    assert bot.answers
    assert len(bot.messages) == 1


def test_page_callback_handles_expired_context(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(pagination_callbacks, "get_user_language", lambda user_id: "en")

    pagination_callbacks.handle_page_callback(bot, fake_call(), 1)

    assert bot.answers[-1][1]["show_alert"] is True


def test_page_callback_edits_current_page(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(pagination_callbacks, "get_user_language", lambda user_id: "en")
    save_search_context(123, "SOS", [sample_track, sample_track | {"deezer_track_id": "2"}])

    pagination_callbacks.handle_page_callback(bot, fake_call(), 0)

    assert bot.edited_texts
    assert bot.answers


def test_back_to_results_callback_calls_action(monkeypatch):
    bot = FakeBot()
    called = {}
    monkeypatch.setattr(pagination_callbacks, "get_user_language", lambda user_id: "en")

    import app.bot.actions as action_module

    monkeypatch.setattr(action_module, "send_current_results_page", lambda **kwargs: called.update(kwargs))

    pagination_callbacks.handle_back_to_results_callback(bot, fake_call())

    assert called["user_id"] == 123


def test_favorite_callback_success(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(favorites_callbacks, "upsert_user", lambda user: None)
    monkeypatch.setattr(favorites_callbacks, "get_track", lambda track_id: sample_track)
    monkeypatch.setattr(favorites_callbacks, "save_track", lambda track: None)
    monkeypatch.setattr(favorites_callbacks, "add_favorite", lambda user_id, track: None)
    monkeypatch.setattr(favorites_callbacks, "user_has_search_context", lambda user_id: False)

    favorites_callbacks.handle_favorite_callback(bot, fake_call(), "671298")

    assert bot.edited_markups
    assert bot.answers


def test_remove_favorite_callback_success(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(favorites_callbacks, "get_track", lambda track_id: sample_track)
    monkeypatch.setattr(favorites_callbacks, "save_track", lambda track: None)
    monkeypatch.setattr(favorites_callbacks, "remove_favorite", lambda **kwargs: None)
    monkeypatch.setattr(favorites_callbacks, "user_has_search_context", lambda user_id: True)

    favorites_callbacks.handle_remove_favorite_callback(bot, fake_call(), "671298")

    assert bot.edited_markups


def test_clear_favorites_request_and_confirm(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(favorites_callbacks, "clear_favorites", lambda user_id: None)

    favorites_callbacks.handle_clear_favorites_request_callback(bot, fake_call())
    favorites_callbacks.handle_clear_favorites_confirm_callback(bot, fake_call())

    assert len(bot.edited_texts) == 2


def test_clear_favorites_cancel_handles_empty_and_non_empty(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(favorites_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(favorites_callbacks, "get_favorite_tracks", lambda user_id: [])
    favorites_callbacks.handle_clear_favorites_cancel_callback(bot, fake_call())

    monkeypatch.setattr(favorites_callbacks, "get_favorite_tracks", lambda user_id: [sample_track])
    favorites_callbacks.handle_clear_favorites_cancel_callback(bot, fake_call())

    assert len(bot.edited_texts) == 2


def test_history_search_callback_not_found(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(history_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(history_callbacks, "get_search_query_by_id", lambda **kwargs: None)

    history_callbacks.handle_history_search_callback(bot, fake_call(), "99")

    assert bot.answers[-1][1]["show_alert"] is True


def test_history_search_callback_repeats_query(monkeypatch):
    bot = FakeBot()
    called = {}
    monkeypatch.setattr(history_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(history_callbacks, "get_search_query_by_id", lambda **kwargs: "SOS")
    monkeypatch.setattr(history_callbacks, "upsert_user", lambda user: None)
    monkeypatch.setattr(history_callbacks, "send_search_results", lambda **kwargs: called.update(kwargs))

    history_callbacks.handle_history_search_callback(bot, fake_call(), "1")

    assert called["query"] == "SOS"


def test_clear_history_request_confirm_and_cancel(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(history_callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(history_callbacks, "clear_search_history", lambda user_id: None)
    monkeypatch.setattr(history_callbacks, "get_search_history", lambda user_id, limit: [])

    history_callbacks.handle_clear_history_request_callback(bot, fake_call())
    history_callbacks.handle_clear_history_confirm_callback(bot, fake_call())
    history_callbacks.handle_clear_history_cancel_callback(bot, fake_call())

    assert len(bot.edited_texts) == 3


def test_callback_router_routes_main_actions(monkeypatch):
    bot = FakeBot()
    called = []
    monkeypatch.setattr(callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(callbacks, "show_main_menu", lambda bot, chat_id, user_id: called.append(("main", user_id)))
    monkeypatch.setattr(callbacks, "ask_for_music", lambda bot, chat_id, user_id: called.append(("search", user_id)))

    callbacks.register_callbacks(bot)
    router = bot.callback_handlers[0][1]

    router(fake_call(ACTION_MAIN_MENU))
    router(fake_call(ACTION_SEARCH_AGAIN))
    router(fake_call(ACTION_NOOP))
    router(fake_call("unknown"))

    assert ("main", 123) in called
    assert ("search", 123) in called
    assert len(bot.answers) >= 4


def test_callback_router_routes_prefixed_actions(monkeypatch):
    bot = FakeBot()
    routed = []
    monkeypatch.setattr(callbacks, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(callbacks, "handle_language_callback", lambda bot, call, language_code: routed.append((CB_LANGUAGE, language_code)))
    monkeypatch.setattr(callbacks, "handle_track_callback", lambda bot, call, track_id: routed.append((CB_TRACK, track_id)))
    monkeypatch.setattr(callbacks, "handle_page_callback", lambda bot, call, page: routed.append((CB_PAGE, page)))
    monkeypatch.setattr(callbacks, "handle_back_to_results_callback", lambda bot, call: routed.append((ACTION_BACK_RESULTS, None)))
    monkeypatch.setattr(callbacks, "handle_favorite_callback", lambda bot, call, track_id: routed.append((CB_FAVORITE, track_id)))
    monkeypatch.setattr(callbacks, "handle_remove_favorite_callback", lambda bot, call, track_id: routed.append((CB_UNFAVORITE, track_id)))
    monkeypatch.setattr(callbacks, "handle_lyrics_callback", lambda bot, call, track_id: routed.append((CB_LYRICS, track_id)))
    monkeypatch.setattr(callbacks, "handle_history_search_callback", lambda bot, call, search_id: routed.append((CB_HISTORY, search_id)))
    monkeypatch.setattr(callbacks, "handle_clear_favorites_request_callback", lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_REQUEST, None)))
    monkeypatch.setattr(callbacks, "handle_clear_favorites_confirm_callback", lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_CONFIRM, None)))
    monkeypatch.setattr(callbacks, "handle_clear_favorites_cancel_callback", lambda bot, call: routed.append((ACTION_FAVORITES_CLEAR_CANCEL, None)))
    monkeypatch.setattr(callbacks, "handle_clear_history_request_callback", lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_REQUEST, None)))
    monkeypatch.setattr(callbacks, "handle_clear_history_confirm_callback", lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_CONFIRM, None)))
    monkeypatch.setattr(callbacks, "handle_clear_history_cancel_callback", lambda bot, call: routed.append((ACTION_HISTORY_CLEAR_CANCEL, None)))

    callbacks.register_callbacks(bot)
    router = bot.callback_handlers[0][1]

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
        router(fake_call(data))

    assert (CB_LANGUAGE, "uk") in routed
    assert (CB_PAGE, 2) in routed
    assert (ACTION_HISTORY_CLEAR_CANCEL, None) in routed
