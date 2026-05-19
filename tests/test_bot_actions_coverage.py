from types import SimpleNamespace

from app.bot import actions
from app.bot.context import save_search_context


class FakeBot:
    def __init__(self):
        self.messages = []
        self.photos = []
        self.next_handlers = []
        self.raise_photo = False

    def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))
        chat_id = kwargs.get("chat_id", args[0] if args else 1)
        return SimpleNamespace(chat=SimpleNamespace(id=chat_id), message_id=len(self.messages))

    def send_photo(self, *args, **kwargs):
        if self.raise_photo:
            raise RuntimeError("photo failed")
        self.photos.append((args, kwargs))

    def register_next_step_handler(self, sent_msg, handler):
        self.next_handlers.append((sent_msg, handler))


def test_show_main_menu_uses_user_language(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "uk")

    actions.show_main_menu(bot, chat_id=10, user_id=123)

    assert bot.messages
    assert bot.messages[0][1]["reply_markup"] is not None


def test_ask_for_music_registers_next_step(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")

    actions.ask_for_music(bot, chat_id=10, user_id=123)

    assert len(bot.messages) == 2
    assert len(bot.next_handlers) == 1


def test_send_search_results_rejects_empty_query(monkeypatch):
    bot = FakeBot()
    called = {"ask": False}
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "ask_for_music", lambda *args, **kwargs: called.update(ask=True))

    actions.send_search_results(bot, chat_id=10, user_id=123, query="   ")

    assert bot.messages
    assert called["ask"] is True


def test_send_search_results_handles_no_results(monkeypatch):
    bot = FakeBot()
    called = {"saved": False, "ask": False}
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "save_search", lambda user_id, query: called.update(saved=True))
    monkeypatch.setattr(actions, "search_tracks", lambda query, limit: [])
    monkeypatch.setattr(actions, "ask_for_music", lambda *args, **kwargs: called.update(ask=True))

    actions.send_search_results(bot, chat_id=10, user_id=123, query="SOS")

    assert called == {"saved": True, "ask": True}
    assert bot.messages


def test_send_search_results_saves_context_and_sends_keyboard(monkeypatch, sample_track):
    bot = FakeBot()
    tracks = [sample_track | {"deezer_track_id": str(index), "title": f"Track {index}"} for index in range(3)]

    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "save_search", lambda user_id, query: None)
    monkeypatch.setattr(actions, "search_tracks", lambda query, limit: tracks)

    actions.send_search_results(bot, chat_id=10, user_id=123, query="SOS")

    assert actions.get_search_context(123)["query"] == "SOS"
    assert bot.messages[-1][1]["reply_markup"] is not None


def test_send_current_results_page_handles_missing_context(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")

    actions.send_current_results_page(bot, chat_id=10, user_id=123)

    assert bot.messages


def test_send_current_results_page_sends_saved_context(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    save_search_context(123, "SOS", [sample_track])

    actions.send_current_results_page(bot, chat_id=10, user_id=123)

    assert bot.messages[-1][1]["reply_markup"] is not None


def test_send_track_card_sends_photo_when_cover_is_available(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: False)
    monkeypatch.setattr(actions, "user_has_search_context", lambda user_id: False)

    actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert bot.photos
    assert not bot.messages


def test_send_track_card_falls_back_to_message_when_photo_fails(monkeypatch, sample_track):
    bot = FakeBot()
    bot.raise_photo = True
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: True)
    monkeypatch.setattr(actions, "user_has_search_context", lambda user_id: True)

    actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert bot.messages[-1][1]["text"] == "formatted"
