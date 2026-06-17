import pytest

from app import main


class FakeSession:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class FakeBot:
    def __init__(self, token="test-token"):
        self.token = token
        self.session = FakeSession()
        self.deleted_webhook_kwargs: dict = {}

    async def delete_webhook(self, **kwargs):
        self.deleted_webhook_kwargs.update(kwargs)


def test_create_bot_validates_settings_and_uses_token(monkeypatch):
    calls = []

    monkeypatch.setattr(main.settings, "BOT_TOKEN", "bot-token")
    monkeypatch.setattr(main.settings, "validate", lambda: calls.append("validate"))
    monkeypatch.setattr(main, "Bot", lambda token: FakeBot(token))

    bot = main.create_bot()

    assert calls == ["validate"]
    assert bot.token == "bot-token"


@pytest.mark.asyncio
async def test_run_bot_initializes_and_polls(monkeypatch):
    bot = FakeBot()
    calls = []

    async def fake_init_db_pool():
        calls.append("init_db_pool")

    async def fake_close_db_pool():
        calls.append("close_db_pool")

    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)

    async def fake_start_polling(self, *bots, **kwargs):
        calls.append(("start_polling", bots))

    monkeypatch.setattr(main.Dispatcher, "start_polling", fake_start_polling)

    await main.run_bot()

    assert "init_db_pool" in calls
    assert ("start_polling", (bot,)) in calls
    assert "close_db_pool" in calls
    assert bot.session.closed is True
    assert bot.deleted_webhook_kwargs.get("drop_pending_updates") is True


@pytest.mark.asyncio
async def test_run_bot_includes_routers_and_drops_pending_updates(monkeypatch):
    bot = FakeBot()
    included = []

    async def fake_init_db_pool():
        pass

    async def fake_close_db_pool():
        pass

    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)

    def patched_include(self, router):
        included.append(router.name)

    monkeypatch.setattr(main.Dispatcher, "include_router", patched_include)

    async def fake_start_polling(self, *bots, **kwargs):
        pass

    monkeypatch.setattr(main.Dispatcher, "start_polling", fake_start_polling)

    await main.run_bot()

    assert "handlers" in included
    assert "callbacks" in included
    assert bot.deleted_webhook_kwargs.get("drop_pending_updates") is True


@pytest.mark.asyncio
async def test_run_bot_logs_and_reraises_polling_error(monkeypatch):
    bot = FakeBot()
    captured = {}

    async def fake_init_db_pool():
        pass

    async def fake_close_db_pool():
        pass

    async def fake_log_and_save_error(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)

    async def fake_start_polling(self, *bots, **kwargs):
        raise RuntimeError("polling failed")

    monkeypatch.setattr(main.Dispatcher, "start_polling", fake_start_polling)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)

    with pytest.raises(RuntimeError, match="polling failed"):
        await main.run_bot()

    assert captured["telegram_id"] is None
    assert captured["source"] == "start_polling"
    assert isinstance(captured["error"], RuntimeError)
    assert bot.session.closed is True


def test_main_runs_run_bot_via_asyncio(monkeypatch):
    calls = []

    async def fake_run_bot():
        calls.append("run_bot")

    monkeypatch.setattr(main, "run_bot", fake_run_bot)

    main.main()

    assert calls == ["run_bot"]
