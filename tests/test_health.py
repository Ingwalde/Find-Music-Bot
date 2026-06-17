import pytest

from app.health import HealthItem, format_health_report


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
