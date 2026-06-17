"""
Integration tests for async PostgreSQL health.py.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.
"""

import pytest

from app.health import check_database, format_health_report


@pytest.mark.asyncio
async def test_check_database_returns_ok_item(live_pg):
    item = await check_database()

    assert item.ok is True
    assert item.name == "Database"
    assert "OK" in item.message


@pytest.mark.asyncio
async def test_format_health_report_contains_database_ok(live_pg):
    report = await format_health_report()

    assert "Find Music Bot health check" in report
    assert "✅ Database:" in report
