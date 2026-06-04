from app import admin_tools
from app.database import repositories as repo


def test_get_spotify_status_text_not_configured(monkeypatch):
    monkeypatch.setattr(admin_tools, "is_spotify_configured", lambda: False)

    assert admin_tools.get_spotify_status_text() == "not configured or disabled"


def test_get_spotify_status_text_available(monkeypatch):
    monkeypatch.setattr(admin_tools, "is_spotify_configured", lambda: True)
    monkeypatch.setattr(admin_tools, "is_spotify_temporarily_blocked", lambda: False)

    assert admin_tools.get_spotify_status_text() == "available"


def test_get_spotify_status_text_blocked(monkeypatch):
    monkeypatch.setattr(admin_tools, "is_spotify_configured", lambda: True)
    monkeypatch.setattr(admin_tools, "is_spotify_temporarily_blocked", lambda: True)
    monkeypatch.setattr(admin_tools, "get_spotify_block_reason", lambda: "403")

    assert "temporarily disabled" in admin_tools.get_spotify_status_text()
    assert "403" in admin_tools.get_spotify_status_text()


def test_format_stats_report(temp_database, fake_user, sample_track, monkeypatch):
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "available")
    repo.upsert_user(fake_user)
    repo.save_search(fake_user.id, "SOS")
    repo.add_favorite(fake_user.id, sample_track)
    repo.save_error(fake_user.id, "unit", "boom")

    report = admin_tools.format_stats_report()

    assert "Bot Statistics" in report
    assert "Users: 1" in report
    assert "Searches: 1" in report
    assert "Favorites: 1" in report
    assert "Tracks cached: 1" in report
    assert "Errors stored: 1" in report
    assert "Spotify status: available" in report


def test_format_maintenance_report(temp_database, monkeypatch):
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "available")

    report = admin_tools.format_maintenance_report()

    assert "Maintenance Report" in report
    assert "Version:" in report
    assert "Schema version:" in report
    assert "Database:" in report
    assert "Spotify: available" in report


def test_format_cleanup_result():
    report = admin_tools.format_cleanup_result(
        "Cleanup done",
        {"before": 5, "after": 2, "deleted": 3},
    )

    assert "Cleanup done" in report
    assert "Before: 5" in report
    assert "Deleted: 3" in report
    assert "After: 2" in report


def test_cleanup_reports(monkeypatch):
    monkeypatch.setattr(admin_tools, "cleanup_old_errors", lambda: {"before": 2, "after": 1, "deleted": 1})
    monkeypatch.setattr(admin_tools, "cleanup_search_history", lambda: {"before": 4, "after": 2, "deleted": 2})

    assert "Error cleanup completed" in admin_tools.cleanup_errors_report()
    assert "Search history cleanup completed" in admin_tools.cleanup_history_report()


def test_admin_reports_support_ukrainian_labels(temp_database, monkeypatch):
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "доступний")

    report = admin_tools.format_stats_report("uk")

    assert "Статистика бота" in report
    assert "Статус Spotify" in report


def test_reload_admins_report_clears_cache(monkeypatch):
    called = {"value": False}

    def fake_clear_cache():
        called["value"] = True

    monkeypatch.setattr(admin_tools, "clear_admin_ids_cache", fake_clear_cache)

    report = admin_tools.reload_admins_report("en")

    assert called["value"] is True
    assert "reloaded" in report.lower()
