"""
Integration tests for admin_audit repository.
Uses the compose "test-postgres" service via the shared live_pg fixture.
"""
import pytest

import app.database.repository_modules.admin_audit as audit_module


@pytest.mark.asyncio
async def test_save_and_get_admin_audit(live_pg):
    await audit_module.save_admin_audit(
        admin_telegram_id=42,
        action="admin_stats",
    )

    rows = await audit_module.get_recent_admin_audit(limit=5)
    assert len(rows) == 1
    assert rows[0]["admin_telegram_id"] == 42
    assert rows[0]["action"] == "admin_stats"
    assert rows[0]["details"] is None


@pytest.mark.asyncio
async def test_save_admin_audit_with_details(live_pg):
    await audit_module.save_admin_audit(
        admin_telegram_id=7,
        action="admin_cleanup_errors",
        details={"rows_deleted": 12},
    )

    rows = await audit_module.get_recent_admin_audit(limit=5)
    assert len(rows) == 1
    assert rows[0]["details"] == {"rows_deleted": 12}


@pytest.mark.asyncio
async def test_get_recent_admin_audit_orders_newest_first(live_pg):
    await audit_module.save_admin_audit(admin_telegram_id=1, action="admin_stats")
    await audit_module.save_admin_audit(admin_telegram_id=1, action="admin_health")

    rows = await audit_module.get_recent_admin_audit(limit=10)
    assert rows[0]["action"] == "admin_health"
    assert rows[1]["action"] == "admin_stats"


@pytest.mark.asyncio
async def test_get_recent_admin_audit_respects_limit(live_pg):
    for i in range(5):
        await audit_module.save_admin_audit(admin_telegram_id=1, action=f"action_{i}")

    rows = await audit_module.get_recent_admin_audit(limit=3)
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_get_recent_admin_audit_empty_table(live_pg):
    rows = await audit_module.get_recent_admin_audit(limit=10)
    assert rows == []
