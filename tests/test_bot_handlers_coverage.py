from types import SimpleNamespace

from app.bot import handlers


class FakeBot:
    def __init__(self):
        self.messages = []
        self.next_handlers = []
        self.message_handlers = []

    def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))
        chat_id = kwargs.get("chat_id", args[0] if args else 1)
        return SimpleNamespace(chat=SimpleNamespace(id=chat_id), message_id=len(self.messages))

    def register_next_step_handler(self, sent_msg, handler):
        self.next_handlers.append((sent_msg, handler))

    def message_handler(self, **decorator_kwargs):
        def decorator(func):
            self.message_handlers.append((decorator_kwargs, func))
            return func

        return decorator


def fake_message(text="SOS", user_id=123):
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        chat=SimpleNamespace(id=10),
    )


def get_registered_handler(bot, name):
    for _metadata, func in bot.message_handlers:
        if func.__name__ == name:
            return func
    raise AssertionError(f"Handler {name} was not registered")


def test_is_admin_uses_settings(monkeypatch):
    monkeypatch.setattr(handlers.settings, "ADMIN_ID", 123)

    assert handlers.is_admin(123) is True
    assert handlers.is_admin(999) is False


def test_format_recent_errors_handles_empty_and_items(monkeypatch):
    monkeypatch.setattr(handlers, "get_recent_errors", lambda limit: [])
    assert handlers.format_recent_errors("en")

    monkeypatch.setattr(
        handlers,
        "get_recent_errors",
        lambda limit: [
            {
                "source": "unit",
                "created_at": "today",
                "error_message": "boom",
                "telegram_id": 123,
            }
        ],
    )
    formatted = handlers.format_recent_errors("en")

    assert "unit" in formatted
    assert "boom" in formatted
    assert "123" in formatted


def test_show_language_menu(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")

    handlers.show_language_menu(bot, fake_message())

    assert bot.messages[-1][1]["reply_markup"] is not None


def test_process_music_search_rejects_non_text(monkeypatch):
    bot = FakeBot()
    called = {}
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "ask_for_music", lambda bot, chat_id, user_id: called.update(asked=True))

    handlers.process_music_search(bot, fake_message(text=None))

    assert called["asked"] is True


def test_process_music_search_routes_menu_buttons(monkeypatch):
    bot = FakeBot()
    called = []
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: "main_menu")
    monkeypatch.setattr(handlers, "show_main_menu", lambda bot, chat_id, user_id: called.append("main"))

    handlers.process_music_search(bot, fake_message(text="Main menu"))

    assert called == ["main"]


def test_process_music_search_disables_other_menu_buttons(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: "favorites")

    handlers.process_music_search(bot, fake_message(text="Favorites"))

    assert len(bot.messages) == 2
    assert len(bot.next_handlers) == 1


def test_process_music_search_handles_start_and_regular_query(monkeypatch):
    bot = FakeBot()
    called = {}
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: None)
    monkeypatch.setattr(handlers, "send_search_results", lambda **kwargs: called.update(kwargs))

    handlers.process_music_search(bot, fake_message(text="/start"))
    handlers.process_music_search(bot, fake_message(text="SOS"))

    assert bot.messages
    assert called["query"] == "SOS"


def test_process_music_search_handles_search_error(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: None)
    monkeypatch.setattr(handlers, "send_search_results", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(handlers, "log_and_save_error", lambda **kwargs: None)

    handlers.process_music_search(bot, fake_message(text="SOS"))

    assert bot.messages


def test_show_favorites_empty_and_with_tracks(monkeypatch, sample_track):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")

    monkeypatch.setattr(handlers, "get_favorite_tracks", lambda user_id: [])
    handlers.show_favorites(bot, fake_message())

    monkeypatch.setattr(handlers, "get_favorite_tracks", lambda user_id: [sample_track])
    handlers.show_favorites(bot, fake_message())

    assert len(bot.messages) >= 4
    assert bot.messages[-1][1]["reply_markup"] is not None


def test_show_favorites_handles_error(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "log_and_save_error", lambda **kwargs: None)

    handlers.show_favorites(bot, fake_message())

    assert bot.messages


def test_show_history_empty_and_with_items(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")

    monkeypatch.setattr(handlers, "get_search_history", lambda user_id, limit: [])
    handlers.show_history(bot, fake_message())

    monkeypatch.setattr(handlers, "get_search_history", lambda user_id, limit: [{"id": 1, "query": "SOS"}])
    handlers.show_history(bot, fake_message())

    assert len(bot.messages) >= 4
    assert bot.messages[-1][1]["reply_markup"] is not None


def test_show_history_handles_error(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "log_and_save_error", lambda **kwargs: None)

    handlers.show_history(bot, fake_message())

    assert bot.messages


def test_register_handlers_command_handlers(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "format_recent_errors", lambda language: "errors")
    monkeypatch.setattr(handlers, "format_health_report", lambda: "health")
    monkeypatch.setattr(handlers, "clear_errors", lambda: None)
    monkeypatch.setattr(handlers.settings, "ADMIN_ID", 123)
    monkeypatch.setattr(handlers, "show_favorites", lambda bot, message: bot.send_message(message.chat.id, "favorites"))
    monkeypatch.setattr(handlers, "show_history", lambda bot, message: bot.send_message(message.chat.id, "history"))
    monkeypatch.setattr(handlers, "show_language_menu", lambda bot, message: bot.send_message(message.chat.id, "language"))

    handlers.register_handlers(bot)

    for handler_name in [
        "start_handler",
        "help_handler",
        "language_handler",
        "version_handler",
        "errors_handler",
        "clear_errors_handler",
        "health_handler",
        "favorites_handler",
        "history_handler",
    ]:
        get_registered_handler(bot, handler_name)(fake_message())

    assert len(bot.messages) >= 9


def test_register_handlers_text_handler_routes_actions(monkeypatch):
    bot = FakeBot()
    routed = []
    actions = iter(["main_menu", "music", "favorites", "history", "language", None])
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_menu_action_by_text", lambda text: next(actions))
    monkeypatch.setattr(handlers, "show_main_menu", lambda bot, chat_id, user_id: routed.append("main"))
    monkeypatch.setattr(handlers, "ask_for_music", lambda bot, chat_id, user_id: routed.append("music"))
    monkeypatch.setattr(handlers, "show_favorites", lambda bot, message: routed.append("favorites"))
    monkeypatch.setattr(handlers, "show_history", lambda bot, message: routed.append("history"))
    monkeypatch.setattr(handlers, "show_language_menu", lambda bot, message: routed.append("language"))
    monkeypatch.setattr(handlers, "process_music_search", lambda bot, message: routed.append("search"))

    handlers.register_handlers(bot)
    text_handler = get_registered_handler(bot, "text_handler")

    for _ in range(6):
        text_handler(fake_message())

    assert routed == ["main", "music", "favorites", "history", "language", "search"]
