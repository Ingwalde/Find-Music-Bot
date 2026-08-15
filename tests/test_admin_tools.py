import pytest

from app import admin_tools


def _fake_summary():
    return {
        "database_path": "testdb",
        "database_size_bytes": 1024,
        "database_size": "1.0 KB",
        "table_counts": {"users": 1, "searches": 1, "favorites": 1, "tracks": 1, "errors": 1},
        "schema_version": "0.0.0-test",
        "app_version": "0.0.0-test",
    }


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


@pytest.mark.asyncio
async def test_format_stats_report(monkeypatch):
    async def fake_get_database_summary():
        return _fake_summary()

    monkeypatch.setattr(admin_tools, "get_database_summary", fake_get_database_summary)
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "available")

    report = await admin_tools.format_stats_report()

    assert "Bot Statistics" in report
    assert "Users: 1" in report
    assert "Searches: 1" in report
    assert "Favorites: 1" in report
    assert "Tracks cached: 1" in report
    assert "Errors stored: 1" in report
    assert "Spotify status: available" in report


@pytest.mark.asyncio
async def test_format_maintenance_report(monkeypatch):
    async def fake_get_database_summary():
        return _fake_summary()

    monkeypatch.setattr(admin_tools, "get_database_summary", fake_get_database_summary)
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "available")

    report = await admin_tools.format_maintenance_report()

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


@pytest.mark.asyncio
async def test_cleanup_reports(monkeypatch):
    async def fake_cleanup_old_errors(*args, **kwargs):
        return {"before": 2, "after": 1, "deleted": 1}

    async def fake_cleanup_search_history(*args, **kwargs):
        return {"before": 4, "after": 2, "deleted": 2}

    cache_pruned = {"called": False}

    async def fake_cleanup_expired_search_cache(*args, **kwargs):
        cache_pruned["called"] = True
        return {"before": 9, "after": 3, "deleted": 6}

    monkeypatch.setattr(admin_tools, "cleanup_old_errors", fake_cleanup_old_errors)
    monkeypatch.setattr(admin_tools, "cleanup_search_history", fake_cleanup_search_history)
    monkeypatch.setattr(
        admin_tools, "cleanup_expired_search_cache", fake_cleanup_expired_search_cache
    )

    assert "Error cleanup completed" in await admin_tools.cleanup_errors_report()

    report = await admin_tools.cleanup_history_report()
    assert "Search history cleanup completed" in report

    # The cache prune rides along with the history cleanup, but the reported
    # counts must stay the history's own — not the cache's.
    assert cache_pruned["called"] is True
    assert "Before: 4" in report
    assert "Deleted: 2" in report
    assert "After: 2" in report


@pytest.mark.asyncio
async def test_admin_reports_support_ukrainian_labels(monkeypatch):
    async def fake_get_database_summary():
        return {
            "database_path": "testdb",
            "database_size_bytes": 0,
            "database_size": "0 B",
            "table_counts": {"users": 0, "searches": 0, "favorites": 0, "tracks": 0, "errors": 0},
            "schema_version": "0.0.0-test",
            "app_version": "0.0.0-test",
        }

    monkeypatch.setattr(admin_tools, "get_database_summary", fake_get_database_summary)
    monkeypatch.setattr(admin_tools, "get_spotify_status_text", lambda language="en": "доступний")

    report = await admin_tools.format_stats_report("uk")

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
