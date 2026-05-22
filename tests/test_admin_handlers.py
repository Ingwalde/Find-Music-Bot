from types import SimpleNamespace

from app.bot import handlers


class FakeBot:
    def __init__(self):
        self.messages = []
        self.message_handlers = []

    def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))
        chat_id = kwargs.get("chat_id", args[0] if args else 1)
        return SimpleNamespace(chat=SimpleNamespace(id=chat_id), message_id=len(self.messages))

    def message_handler(self, **decorator_kwargs):
        def decorator(func):
            self.message_handlers.append((decorator_kwargs, func))
            return func

        return decorator


def fake_message(user_id=123):
    return SimpleNamespace(
        text="/stats",
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        chat=SimpleNamespace(id=10),
    )


def get_registered_handler(bot, name):
    for _metadata, func in bot.message_handlers:
        if func.__name__ == name:
            return func
    raise AssertionError(f"Handler {name} was not registered")


def test_admin_handlers_return_admin_reports(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers.settings, "ADMIN_ID", 123)
    monkeypatch.setattr(handlers, "format_stats_report", lambda: "stats report")
    monkeypatch.setattr(handlers, "format_maintenance_report", lambda: "maintenance report")
    monkeypatch.setattr(handlers, "cleanup_errors_report", lambda: "errors cleanup")
    monkeypatch.setattr(handlers, "cleanup_history_report", lambda: "history cleanup")

    handlers.register_handlers(bot)

    for handler_name in [
        "stats_handler",
        "maintenance_handler",
        "cleanup_errors_handler",
        "cleanup_history_handler",
    ]:
        get_registered_handler(bot, handler_name)(fake_message(user_id=123))

    sent_texts = [args[1] for args, _kwargs in bot.messages]

    assert "stats report" in sent_texts
    assert "maintenance report" in sent_texts
    assert "errors cleanup" in sent_texts
    assert "history cleanup" in sent_texts


def test_admin_handlers_reject_non_admin(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers.settings, "ADMIN_ID", 123)

    handlers.register_handlers(bot)

    get_registered_handler(bot, "stats_handler")(fake_message(user_id=999))
    get_registered_handler(bot, "maintenance_handler")(fake_message(user_id=999))

    sent_texts = [args[1] for args, _kwargs in bot.messages]

    assert all("admin" in text.lower() or "only" in text.lower() for text in sent_texts)
