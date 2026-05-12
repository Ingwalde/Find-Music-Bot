from app.health import HealthItem, format_health_report


def test_format_health_report_contains_core_items(monkeypatch):
    monkeypatch.setattr(
        "app.health.get_health_items",
        lambda: [
            HealthItem("Bot", True, "OK"),
            HealthItem("Database", True, "OK"),
            HealthItem("Spotify", False, "Temporarily unavailable"),
        ],
    )

    report = format_health_report()

    assert "Find Music Bot health check" in report
    assert "✅ Bot: OK" in report
    assert "✅ Database: OK" in report
    assert "⚠️ Spotify: Temporarily unavailable" in report
