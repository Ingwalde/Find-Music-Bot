import pytest

from app.database import repositories as repo
from app.database.db import get_connection
from app.database.maintenance import (
    cleanup_old_errors,
    cleanup_search_history,
    format_bytes,
    get_database_size_bytes,
    get_database_summary,
    get_maintenance_table_names,
    get_schema_version,
    get_table_count,
    get_table_counts,
)


def test_format_bytes_formats_expected_units():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"

    with pytest.raises(ValueError):
        format_bytes(-1)


def test_schema_version_is_recorded_by_init_db(temp_database):
    assert get_schema_version()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM schema_migrations")
    row = cursor.fetchone()
    conn.close()

    assert row["count"] >= 1


def test_database_summary_contains_counts(temp_database, fake_user, sample_track):
    repo.upsert_user(fake_user)
    repo.save_search(fake_user.id, "SOS")
    repo.add_favorite(fake_user.id, sample_track)
    repo.save_error(fake_user.id, "unit", "boom")

    summary = get_database_summary()

    assert summary["database_size_bytes"] == get_database_size_bytes()
    assert summary["table_counts"]["users"] == 1
    assert summary["table_counts"]["searches"] == 1
    assert summary["table_counts"]["favorites"] == 1
    assert summary["table_counts"]["errors"] == 1
    assert summary["schema_version"]


def test_get_table_count_rejects_unknown_table(temp_database):
    with pytest.raises(ValueError):
        get_table_count("not_a_real_table")


def test_get_table_counts_returns_known_tables(temp_database):
    counts = get_table_counts()

    assert "users" in counts
    assert "schema_migrations" in counts


def test_cleanup_old_errors_keeps_latest_rows(temp_database):
    for index in range(5):
        repo.save_error(telegram_id=index, source="unit", error_message=f"error {index}")

    result = cleanup_old_errors(keep_latest=2)

    assert result == {"before": 5, "after": 2, "deleted": 3}
    assert len(repo.get_recent_errors(limit=10)) == 2


def test_cleanup_old_errors_can_clear_all_rows(temp_database):
    repo.save_error(telegram_id=1, source="unit", error_message="error")

    result = cleanup_old_errors(keep_latest=0)

    assert result == {"before": 1, "after": 0, "deleted": 1}


def test_cleanup_old_errors_rejects_negative_limit(temp_database):
    with pytest.raises(ValueError):
        cleanup_old_errors(keep_latest=-1)


def test_cleanup_search_history_keeps_latest_rows_per_user(temp_database, fake_user, monkeypatch):
    monkeypatch.setattr("app.config.settings.settings.MAX_HISTORY_PER_USER", 10)
    repo.upsert_user(fake_user)

    for index in range(5):
        repo.save_search(fake_user.id, f"query {index}")

    result = cleanup_search_history(max_rows_per_user=2)

    assert result == {"before": 5, "after": 2, "deleted": 3}
    assert len(repo.get_search_history(fake_user.id, limit=10)) == 2


def test_cleanup_search_history_can_clear_all_rows(temp_database, fake_user, monkeypatch):
    monkeypatch.setattr("app.config.settings.settings.MAX_HISTORY_PER_USER", 10)
    repo.upsert_user(fake_user)
    repo.save_search(fake_user.id, "SOS")

    result = cleanup_search_history(max_rows_per_user=0)

    assert result == {"before": 1, "after": 0, "deleted": 1}


def test_cleanup_search_history_rejects_negative_limit(temp_database):
    with pytest.raises(ValueError):
        cleanup_search_history(max_rows_per_user=-1)


def test_maintenance_table_names_are_discovered_from_sqlite_schema(temp_database):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS custom_runtime_table (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    assert "custom_runtime_table" in get_maintenance_table_names()
    assert get_table_count("custom_runtime_table") == 0
