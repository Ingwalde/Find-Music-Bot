import asyncio

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
        self.set_webhook_kwargs: dict = {}

    async def delete_webhook(self, **kwargs):
        self.deleted_webhook_kwargs.update(kwargs)

    async def set_webhook(self, url, **kwargs):
        self.set_webhook_kwargs = {"url": url, **kwargs}


class FakeMonitoringServer:
    """
    Stand-in for the uvicorn.Server returned by main._create_monitoring_server.

    By default `.serve()` hangs (like the real uvicorn server keeps running
    until told to stop) so tests can observe whether it gets cancelled
    cleanly when the other task finishes first. `serve_behavior` lets a test
    override that: "raise" makes it raise `error`, "return" makes it return
    None immediately (simulating uvicorn's own SIGTERM/SIGINT handling having
    already set should_exit=True and returned normally).
    """

    def __init__(self, serve_behavior="hang", error=None):
        self.serve_behavior = serve_behavior
        self.error = error
        self.cancelled = False
        self.started = False

    async def serve(self):
        self.started = True
        if self.serve_behavior == "raise":
            raise self.error
        if self.serve_behavior == "return":
            return None
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class HangingPolling:
    """
    Stand-in for Dispatcher.start_polling that hangs until cancelled, so
    tests can verify the polling task is actually cancelled (not leaked)
    when the monitoring task finishes first.
    """

    def __init__(self):
        self.cancelled = False

    async def __call__(self, *bots, **kwargs):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class HangingWebhookServer:
    """
    Stand-in for app.webhook.run_webhook_server: hangs until cancelled, so
    tests can verify the webhook task is actually cancelled (not leaked)
    when the monitoring task finishes first — mirrors HangingPolling.
    """

    def __init__(self):
        self.cancelled = False
        self.called_with = None

    async def __call__(self, bot, dispatcher):
        self.called_with = (bot, dispatcher)
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


def _set_webhook_mode(monkeypatch):
    monkeypatch.setattr(main.settings, "BOT_MODE", "webhook")
    monkeypatch.setattr(main.settings, "WEBHOOK_PUBLIC_URL", "https://example.com:8443")
    monkeypatch.setattr(main.settings, "WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.setattr(main.settings, "WEBHOOK_SECRET_TOKEN", "secret-token")
    monkeypatch.setattr(main.settings, "WEBHOOK_CERT_PATH", "/certs/cert.pem")
    monkeypatch.setattr(main.settings, "WEBHOOK_KEY_PATH", "/certs/key.pem")
    monkeypatch.setattr(main.settings, "WEBHOOK_PORT", 8443)
    monkeypatch.setattr(main, "FSInputFile", lambda path: f"cert:{path}")


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
    fake_server = FakeMonitoringServer()

    async def fake_init_db_pool():
        calls.append("init_db_pool")

    async def fake_close_db_pool():
        calls.append("close_db_pool")

    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)

    async def fake_start_polling(self, *bots, **kwargs):
        calls.append(("start_polling", bots))

    monkeypatch.setattr(main.Dispatcher, "start_polling", fake_start_polling)

    await main.run_bot()

    assert "init_db_pool" in calls
    assert ("start_polling", (bot,)) in calls
    assert "close_db_pool" in calls
    assert bot.session.closed is True
    assert bot.deleted_webhook_kwargs.get("drop_pending_updates") is True
    assert fake_server.started is True
    assert fake_server.cancelled is True


@pytest.mark.asyncio
async def test_run_bot_includes_routers_and_drops_pending_updates(monkeypatch):
    bot = FakeBot()
    included = []
    fake_server = FakeMonitoringServer()

    async def fake_init_db_pool():
        pass

    async def fake_close_db_pool():
        pass

    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)

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
    assert fake_server.cancelled is True


@pytest.mark.asyncio
async def test_run_bot_logs_and_reraises_polling_error(monkeypatch):
    bot = FakeBot()
    captured = {}
    fake_server = FakeMonitoringServer()

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
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)

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
    assert fake_server.cancelled is True


@pytest.mark.asyncio
async def test_run_bot_logs_polling_error_and_cancels_running_monitoring(monkeypatch):
    """
    Polling fails while monitoring is still running: source must be
    "start_polling", the monitoring task must be cancelled (not leaked),
    cleanup must still run, and the original exception must re-raise.
    """
    bot = FakeBot()
    captured = {}
    fake_server = FakeMonitoringServer(serve_behavior="hang")

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
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)

    async def fake_start_polling(self, *bots, **kwargs):
        raise RuntimeError("polling failed")

    monkeypatch.setattr(main.Dispatcher, "start_polling", fake_start_polling)

    with pytest.raises(RuntimeError, match="polling failed"):
        await main.run_bot()

    assert captured["telegram_id"] is None
    assert captured["source"] == "start_polling"
    assert isinstance(captured["error"], RuntimeError)
    assert fake_server.started is True
    assert fake_server.cancelled is True
    assert bot.session.closed is True


@pytest.mark.asyncio
async def test_run_bot_logs_monitoring_error_and_cancels_running_polling(monkeypatch):
    """
    Mirror of the above: monitoring fails while polling is still running.
    source must be "monitoring_server", the polling task must be cancelled
    (not leaked), cleanup must still run, and the original exception must
    re-raise.
    """
    bot = FakeBot()
    captured = {}
    monitoring_error = RuntimeError("monitoring failed")
    fake_server = FakeMonitoringServer(serve_behavior="raise", error=monitoring_error)
    hanging_polling = HangingPolling()

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
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)
    monkeypatch.setattr(main.Dispatcher, "start_polling", hanging_polling)

    with pytest.raises(RuntimeError, match="monitoring failed"):
        await main.run_bot()

    assert captured["telegram_id"] is None
    assert captured["source"] == "monitoring_server"
    assert captured["error"] is monitoring_error
    assert hanging_polling.cancelled is True
    assert bot.session.closed is True


@pytest.mark.asyncio
async def test_run_bot_clean_shutdown_cancels_hanging_polling_without_raising(monkeypatch):
    """
    Regression test for the bug this stage exists to prevent: when uvicorn's
    own signal handling sets should_exit=True and serve() returns normally
    (clean shutdown, no exception), run_bot() must not hang forever on a
    naive asyncio.gather() waiting for the still-running polling task. It
    must cancel the polling task, run cleanup, and return without raising.
    """
    bot = FakeBot()
    captured = {}
    fake_server = FakeMonitoringServer(serve_behavior="return")
    hanging_polling = HangingPolling()

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
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)
    monkeypatch.setattr(main.Dispatcher, "start_polling", hanging_polling)

    await main.run_bot()

    assert captured == {}
    assert hanging_polling.cancelled is True
    assert bot.session.closed is True


@pytest.mark.asyncio
async def test_run_bot_webhook_mode_sets_webhook_and_cancels_cleanly(monkeypatch):
    """
    Mirror of test_run_bot_clean_shutdown_cancels_hanging_polling_without_raising,
    for webhook mode: monitoring finishes cleanly, the webhook task must be
    cancelled (not leaked), bot.set_webhook (not delete_webhook) must have
    been called with the secret token and certificate, and start_polling
    must never run.
    """
    bot = FakeBot()
    fake_server = FakeMonitoringServer(serve_behavior="return")
    hanging_webhook = HangingWebhookServer()
    captured = {}

    async def fake_init_db_pool():
        pass

    async def fake_close_db_pool():
        pass

    async def fake_log_and_save_error(**kwargs):
        captured.update(kwargs)

    async def fail_if_polling_starts(self, *bots, **kwargs):
        pytest.fail("start_polling must not run in webhook mode")

    _set_webhook_mode(monkeypatch)
    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)
    monkeypatch.setattr(main, "run_webhook_server", hanging_webhook)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)
    monkeypatch.setattr(main.Dispatcher, "start_polling", fail_if_polling_starts)

    await main.run_bot()

    assert captured == {}
    assert bot.set_webhook_kwargs["url"] == "https://example.com:8443/secret-path"
    assert bot.set_webhook_kwargs["secret_token"] == "secret-token"
    assert bot.set_webhook_kwargs["certificate"] == "cert:/certs/cert.pem"
    assert bot.set_webhook_kwargs["drop_pending_updates"] is True
    assert bot.deleted_webhook_kwargs == {}
    assert hanging_webhook.cancelled is True
    assert hanging_webhook.called_with[0] is bot
    assert bot.session.closed is True


@pytest.mark.asyncio
async def test_run_bot_logs_webhook_error_and_cancels_running_monitoring(monkeypatch):
    """
    Mirror of test_run_bot_logs_polling_error_and_cancels_running_monitoring,
    for webhook mode: source must be "webhook_server" on failure, not the
    stale "start_polling" default.
    """
    bot = FakeBot()
    captured = {}
    fake_server = FakeMonitoringServer(serve_behavior="hang")

    async def fake_init_db_pool():
        pass

    async def fake_close_db_pool():
        pass

    async def fake_log_and_save_error(**kwargs):
        captured.update(kwargs)

    async def failing_webhook_server(bot, dispatcher):
        raise RuntimeError("webhook failed")

    _set_webhook_mode(monkeypatch)
    monkeypatch.setattr(main, "init_db_pool", fake_init_db_pool)
    monkeypatch.setattr(main, "close_db_pool", fake_close_db_pool)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)
    monkeypatch.setattr(main, "_create_monitoring_server", lambda: fake_server)
    monkeypatch.setattr(main, "run_webhook_server", failing_webhook_server)
    monkeypatch.setattr(main, "log_and_save_error", fake_log_and_save_error)

    with pytest.raises(RuntimeError, match="webhook failed"):
        await main.run_bot()

    assert captured["telegram_id"] is None
    assert captured["source"] == "webhook_server"
    assert isinstance(captured["error"], RuntimeError)
    assert fake_server.started is True
    assert fake_server.cancelled is True
    assert bot.session.closed is True


def test_main_runs_run_bot_via_asyncio(monkeypatch):
    calls = []

    async def fake_run_bot():
        calls.append("run_bot")

    monkeypatch.setattr(main, "run_bot", fake_run_bot)

    main.main()

    assert calls == ["run_bot"]
