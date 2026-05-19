import pytest

from app import main


class FakeTelegramBot:
    def __init__(self, token="test-token", fail_polling=False):
        self.token = token
        self.fail_polling = fail_polling
        self.polling_kwargs = None

    def infinity_polling(self, **kwargs):
        self.polling_kwargs = kwargs
        if self.fail_polling:
            raise RuntimeError("polling failed")


def test_create_bot_validates_settings_and_uses_token(monkeypatch):
    calls = []

    monkeypatch.setattr(main.settings, "BOT_TOKEN", "bot-token")
    monkeypatch.setattr(main.settings, "validate", lambda: calls.append("validate"))
    monkeypatch.setattr(main.telebot, "TeleBot", lambda token: FakeTelegramBot(token))

    bot = main.create_bot()

    assert calls == ["validate"]
    assert bot.token == "bot-token"


def test_run_bot_initializes_registers_and_polls(monkeypatch):
    bot = FakeTelegramBot()
    calls = []

    monkeypatch.setattr(main, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main, "register_handlers", lambda bot_arg: calls.append(("handlers", bot_arg)))
    monkeypatch.setattr(main, "register_callbacks", lambda bot_arg: calls.append(("callbacks", bot_arg)))

    main.run_bot()

    assert calls == ["init_db", ("handlers", bot), ("callbacks", bot)]
    assert bot.polling_kwargs == {
        "timeout": 60,
        "long_polling_timeout": 60,
        "skip_pending": True,
    }


def test_run_bot_logs_and_reraises_polling_error(monkeypatch):
    bot = FakeTelegramBot(fail_polling=True)
    captured = {}

    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main, "register_handlers", lambda bot_arg: None)
    monkeypatch.setattr(main, "register_callbacks", lambda bot_arg: None)
    monkeypatch.setattr(
        main,
        "log_and_save_error",
        lambda **kwargs: captured.update(kwargs),
    )

    with pytest.raises(RuntimeError, match="polling failed"):
        main.run_bot()

    assert captured["telegram_id"] is None
    assert captured["source"] == "infinity_polling"
    assert isinstance(captured["error"], RuntimeError)
