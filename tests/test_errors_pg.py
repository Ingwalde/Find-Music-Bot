"""
Integration tests for async PostgreSQL errors.py repository.
Uses testcontainers (Option A) via the shared live_pg fixture from conftest.py.
"""

import pytest

import app.database.repository_modules.errors as errors_module


@pytest.mark.asyncio
async def test_save_error_and_get_recent(live_pg):
    await errors_module.save_error(
        telegram_id=123,
        source="unit_test",
        error_message="Something failed",
    )

    errors = await errors_module.get_recent_errors(limit=5)

    assert len(errors) == 1
    assert errors[0]["source"] == "unit_test"
    assert errors[0]["error_message"] == "Something failed"
    assert errors[0]["telegram_id"] == 123


@pytest.mark.asyncio
async def test_get_recent_errors_respects_limit(live_pg):
    for i in range(5):
        await errors_module.save_error(
            telegram_id=None,
            source="batch",
            error_message=f"Error {i}",
        )

    errors = await errors_module.get_recent_errors(limit=3)
    assert len(errors) == 3


@pytest.mark.asyncio
async def test_get_recent_errors_orders_newest_first(live_pg):
    await errors_module.save_error(telegram_id=1, source="first", error_message="old")
    await errors_module.save_error(telegram_id=2, source="second", error_message="new")

    errors = await errors_module.get_recent_errors(limit=2)
    assert errors[0]["source"] == "second"


@pytest.mark.asyncio
async def test_clear_errors_empties_table(live_pg):
    await errors_module.save_error(telegram_id=None, source="test", error_message="x")

    await errors_module.clear_errors()

    errors = await errors_module.get_recent_errors(limit=10)
    assert errors == []
