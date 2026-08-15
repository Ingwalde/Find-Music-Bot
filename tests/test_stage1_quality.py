"""Covers the v3.7.10 Stage 1 changes: credential logging, settings, shutdown."""

import os

import pytest

import app.services.redis_client as redis_client
from app.config.settings import Settings
from app.services.redis_client import _safe_target

# ── Redis credentials must never reach the log ───────────────────────────────


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("redis://localhost:6379", "localhost:6379"),
        ("redis://redis:6379/0", "redis:6379"),
        ("redis://host", "host"),
        ("rediss://cache.example.com:6380", "cache.example.com:6380"),
    ],
)
def test_safe_target_keeps_host_and_port(url, expected):
    assert _safe_target(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "redis://:hunter2@localhost:6379",
        "redis://user:hunter2@localhost:6379",
        "rediss://admin:s3cr3t-p4ss@cache.example.com:6380/1",
    ],
)
def test_safe_target_drops_the_password(url):
    """The whole point: a managed Redis puts the password in the URL."""
    result = _safe_target(url)

    assert "hunter2" not in result
    assert "s3cr3t-p4ss" not in result
    assert "@" not in result


def test_safe_target_survives_an_unparseable_url():
    assert _safe_target("://:::") == "<unparseable url>"


class RecordingLogger:
    """
    Captures log calls directly off the module logger.

    caplog cannot be used here: setup_logging() does root_logger.handlers.clear(),
    so any test that reconfigures logging removes caplog's handler and every
    later assertion runs against an empty record list — which made the
    "password must not appear" assertion pass vacuously.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _record(self, msg, *args, **kwargs):
        self.calls.append(msg % args if args else msg)

    info = warning = error = debug = _record


@pytest.mark.asyncio
async def test_init_redis_logs_the_host_not_the_url(monkeypatch):
    """End to end: the password must not appear in what gets logged."""

    class FakeRedis:
        async def ping(self):
            return True

    recorder = RecordingLogger()
    monkeypatch.setattr(redis_client, "logger", recorder)
    monkeypatch.setattr(
        redis_client.aioredis, "from_url", lambda url, **kw: FakeRedis()
    )

    await redis_client.init_redis("redis://:hunter2@cache.internal:6379")
    redis_client._client = None

    logged = " ".join(recorder.calls)

    assert logged, "nothing was logged — the assertions below would pass vacuously"
    assert "hunter2" not in logged
    assert "cache.internal:6379" in logged


# ── Settings must read the environment at construction, not at import ────────


def test_settings_reads_env_at_construction(monkeypatch):
    """
    The reason migrations/env.py had to bypass this class: a bare os.getenv()
    default is evaluated once when the class body runs, so a later change to
    os.environ was invisible even to a fresh Settings().
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql://first@host/db")
    assert Settings().DATABASE_URL == "postgresql://first@host/db"

    monkeypatch.setenv("DATABASE_URL", "postgresql://second@host/db")
    assert Settings().DATABASE_URL == "postgresql://second@host/db"


def test_settings_applies_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("RESULTS_PER_PAGE", raising=False)
    monkeypatch.delenv("BOT_MODE", raising=False)

    settings = Settings()

    assert settings.RESULTS_PER_PAGE == 5
    assert settings.BOT_MODE == "polling"


def test_settings_instances_are_independent(monkeypatch):
    monkeypatch.setenv("MAX_SEARCH_RESULTS", "7")
    first = Settings()
    monkeypatch.setenv("MAX_SEARCH_RESULTS", "9")
    second = Settings()

    assert (first.MAX_SEARCH_RESULTS, second.MAX_SEARCH_RESULTS) == (7, 9)


def test_module_singleton_still_exists():
    """The singleton stays import-time on purpose — config is not runtime state."""
    from app.config.settings import settings

    assert isinstance(settings, Settings)


def test_no_field_default_is_shared_mutable_state():
    """Guards against a factory accidentally returning a shared object."""
    a, b = Settings(), Settings()

    for name in ("BOT_TOKEN", "DATABASE_URL", "REDIS_URL"):
        assert getattr(a, name) == getattr(b, name)


# ── ALEMBIC_DATABASE_URL workaround should now be unnecessary ────────────────


def test_settings_now_sees_a_late_database_url(monkeypatch):
    """
    Documents that the env.py workaround is no longer forced by this class.
    env.py itself is left alone in this stage — changing it is a separate,
    riskier edit touching the migration path.
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql://late@host/db")

    assert Settings().DATABASE_URL == os.environ["DATABASE_URL"]


# ── clean shutdown must be logged, and must still not raise ─────────────────


@pytest.mark.asyncio
async def test_clean_shutdown_is_logged_but_does_not_raise(monkeypatch):
    """
    A task finishing without an exception is the graceful-shutdown path and is
    pinned as "must not raise" by
    test_run_bot_clean_shutdown_cancels_hanging_polling_without_raising.

    The gap was that it left no trace: the process stopped serving with nothing
    in the log saying so. This asserts both halves — a record is emitted, and
    the exit is still clean.
    """
    import app.main as main
    from tests.test_main_runtime import FakeBot, FakeMonitoringServer, HangingPolling

    bot = FakeBot()
    captured: dict = {}
    hanging_polling = HangingPolling()

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(main, "init_db_pool", noop)
    monkeypatch.setattr(main, "close_db_pool", noop)
    monkeypatch.setattr(main, "create_bot", lambda: bot)
    monkeypatch.setattr(main.Dispatcher, "include_router", lambda self, router: None)
    monkeypatch.setattr(
        main, "_create_monitoring_server", lambda: FakeMonitoringServer(serve_behavior="return")
    )
    monkeypatch.setattr(
        main, "log_and_save_error", lambda **kw: captured.update(kw) or noop()
    )
    monkeypatch.setattr(main.Dispatcher, "start_polling", hanging_polling)

    recorder = RecordingLogger()
    monkeypatch.setattr(main, "logger", recorder)

    await main.run_bot()

    assert captured == {}, "clean shutdown must not be recorded as an error"
    assert hanging_polling.cancelled is True

    logged = " ".join(recorder.calls)
    assert logged, "nothing was logged — the assertions below would pass vacuously"
    assert "finished without an exception" in logged, (
        "the shutdown left no trace in the log — the bug this fixes"
    )
    assert "monitoring_server" in logged, "the record must name which half stopped"
