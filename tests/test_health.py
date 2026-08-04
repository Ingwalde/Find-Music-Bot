import pytest

import app.services.redis_client as redis_client_module
from app.health import HealthItem, check_redis, format_health_report


@pytest.mark.asyncio
async def test_check_redis_not_configured_returns_ok(monkeypatch):
    import app.health as health_module

    monkeypatch.setattr(health_module.settings, "REDIS_URL", None)

    item = await check_redis()

    assert item.ok is True
    assert "Not configured" in item.message


@pytest.mark.asyncio
async def test_check_redis_client_none_returns_not_ok(monkeypatch):
    import app.health as health_module

    monkeypatch.setattr(health_module.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", None)

    item = await check_redis()

    assert item.ok is False
    assert "not initialised" in item.message


@pytest.mark.asyncio
async def test_check_redis_ping_ok(monkeypatch):
    import app.health as health_module

    class FakeClient:
        async def ping(self):
            return True

    monkeypatch.setattr(health_module.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", FakeClient())

    item = await check_redis()

    assert item.ok is True
    assert item.message == "OK"


@pytest.mark.asyncio
async def test_check_redis_ping_fails(monkeypatch):
    import app.health as health_module

    class FakeClient:
        async def ping(self):
            raise ConnectionError("refused")

    monkeypatch.setattr(health_module.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", FakeClient())

    item = await check_redis()

    assert item.ok is False
    assert "Unavailable" in item.message


@pytest.mark.asyncio
async def test_format_health_report_contains_core_items(monkeypatch):
    async def fake_get_health_items():
        return [
            HealthItem("Bot", True, "OK"),
            HealthItem("Database", True, "OK"),
            HealthItem("Spotify", False, "Temporarily unavailable"),
        ]

    monkeypatch.setattr("app.health.get_health_items", fake_get_health_items)

    report = await format_health_report()

    assert "Find Music Bot health check" in report
    assert "✅ Bot: OK" in report
    assert "✅ Database: OK" in report
    assert "⚠️ Spotify: Temporarily unavailable" in report
