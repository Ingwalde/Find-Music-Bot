"""
Integration tests for async PostgreSQL maintenance.py.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.

format_bytes (pure sync) is tested in the existing test_database_maintenance.py.
All functions tested here require a live pool — each test gets a clean slate
via the function-scoped live_pg fixture (TRUNCATE including schema_migrations).
"""

from types import SimpleNamespace

import pytest

import app.database.repository_modules.errors as errors_module
import app.database.repository_modules.searches as searches_module
import app.database.repository_modules.users as users_module
from app.database.maintenance import (
    cleanup_old_errors,
    cleanup_search_history,
    get_database_size_bytes,
    get_database_summary,
    get_maintenance_table_names,
    get_schema_version,
    get_table_count,
    get_table_counts,
)
from app.version import __version__


def make_user(user_id: int = 444_555_666, username: str = "maint_user", first_name: str = "Maint"):
    return SimpleNamespace(id=user_id, username=username, first_name=first_name)


# ── get_maintenance_table_names ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_maintenance_table_names_includes_core_tables(live_pg):
    table_names = await get_maintenance_table_names()

    assert "users" in table_names
    assert "tracks" in table_names
    assert "errors" in table_names
    assert "searches" in table_names
    assert "favorites" in table_names


# ── get_table_count ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_table_count_returns_zero_on_empty_table(live_pg):
    count = await get_table_count("users")
    assert count == 0


@pytest.mark.asyncio
async def test_get_table_count_returns_correct_count_after_insert(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    count = await get_table_count("users")
    assert count == 1


@pytest.mark.asyncio
async def test_get_table_count_rejects_unknown_table(live_pg):
    with pytest.raises(ValueError):
        await get_table_count("not_a_real_table")


# ── get_table_counts ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_table_counts_returns_dict_with_known_tables(live_pg):
    counts = await get_table_counts()

    assert "users" in counts
    assert "schema_migrations" in counts
    assert isinstance(counts["users"], int)


# ── get_database_size_bytes ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_database_size_bytes_returns_positive_int(live_pg):
    size = await get_database_size_bytes()

    assert isinstance(size, int)
    assert size > 0


# ── get_schema_version ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_schema_version_returns_app_version():
    version = await get_schema_version()
    assert version == __version__


# ── get_database_summary ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_database_summary_has_expected_keys(live_pg):
    summary = await get_database_summary()

    assert "database_path" in summary
    assert "database_size_bytes" in summary
    assert "database_size" in summary
    assert "table_counts" in summary
    assert "schema_version" in summary
    assert "app_version" in summary


@pytest.mark.asyncio
async def test_get_database_summary_database_path_is_pg_dbname(live_pg):
    summary = await get_database_summary()

    assert isinstance(summary["database_path"], str)
    assert len(summary["database_path"]) > 0


@pytest.mark.asyncio
async def test_get_database_summary_reflects_user_count(live_pg):
    user = make_user()
    await users_module.upsert_user(user)

    summary = await get_database_summary()
    assert summary["table_counts"]["users"] == 1


# ── cleanup_old_errors ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cleanup_old_errors_keeps_latest_rows(live_pg):
    for i in range(5):
        await errors_module.save_error(telegram_id=i, source="unit", error_message=f"error {i}")

    result = await cleanup_old_errors(keep_latest=2)

    assert result == {"before": 5, "after": 2, "deleted": 3}


@pytest.mark.asyncio
async def test_cleanup_old_errors_can_clear_all_rows(live_pg):
    await errors_module.save_error(telegram_id=1, source="unit", error_message="error")

    result = await cleanup_old_errors(keep_latest=0)

    assert result == {"before": 1, "after": 0, "deleted": 1}


@pytest.mark.asyncio
async def test_cleanup_old_errors_rejects_negative_limit(live_pg):
    with pytest.raises(ValueError):
        await cleanup_old_errors(keep_latest=-1)


# ── cleanup_search_history ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cleanup_search_history_keeps_latest_rows_per_user(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    for i in range(5):
        await searches_module.save_search(user.id, f"query {i}")

    result = await cleanup_search_history(max_rows_per_user=2)

    assert result == {"before": 5, "after": 2, "deleted": 3}


@pytest.mark.asyncio
async def test_cleanup_search_history_can_clear_all_rows(live_pg):
    user = make_user()
    await users_module.upsert_user(user)
    await searches_module.save_search(user.id, "SOS")

    result = await cleanup_search_history(max_rows_per_user=0)

    assert result == {"before": 1, "after": 0, "deleted": 1}


@pytest.mark.asyncio
async def test_cleanup_search_history_rejects_negative_limit(live_pg):
    with pytest.raises(ValueError):
        await cleanup_search_history(max_rows_per_user=-1)
