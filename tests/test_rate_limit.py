import pytest

from app.bot import rate_limit
from app.config.settings import settings
from app.localization.translations import t


@pytest.mark.asyncio
async def test_check_rate_limit_allows_under_limit():
    for _ in range(20):
        assert await rate_limit.check_rate_limit(1) is True


@pytest.mark.asyncio
async def test_check_rate_limit_blocks_at_limit():
    for _ in range(20):
        await rate_limit.check_rate_limit(1)

    assert await rate_limit.check_rate_limit(1) is False


@pytest.mark.asyncio
async def test_check_rate_limit_is_per_user():
    for _ in range(20):
        await rate_limit.check_rate_limit(1)

    assert await rate_limit.check_rate_limit(1) is False
    assert await rate_limit.check_rate_limit(2) is True


@pytest.mark.asyncio
async def test_check_rate_limit_sliding_window_clears_old_requests(monkeypatch):
    current = [1000.0]
    monkeypatch.setattr(rate_limit, "time", lambda: current[0])

    for _ in range(20):
        await rate_limit.check_rate_limit(1)

    assert await rate_limit.check_rate_limit(1) is False

    current[0] += settings.RATE_LIMIT_WINDOW_SECONDS + 1

    assert await rate_limit.check_rate_limit(1) is True


@pytest.mark.asyncio
async def test_check_rate_limit_admin_always_allowed():
    for _ in range(25):
        result = await rate_limit.check_rate_limit(99, is_admin=True)
        assert result is True


@pytest.mark.asyncio
async def test_check_rate_limit_resets_warn_flag_on_success():
    await rate_limit.check_rate_limit(1)
    rate_limit._warned_users.add(1)

    await rate_limit.check_rate_limit(1)

    assert 1 not in rate_limit._warned_users


@pytest.mark.asyncio
async def test_should_warn_once_true_first_time_then_false():
    assert await rate_limit.should_warn_once(5) is True
    assert await rate_limit.should_warn_once(5) is False
    assert await rate_limit.should_warn_once(5) is False


@pytest.mark.asyncio
async def test_should_warn_once_is_per_user():
    assert await rate_limit.should_warn_once(5) is True
    assert await rate_limit.should_warn_once(6) is True


def test_rate_limit_exceeded_key_translates_correctly():
    assert t("rate_limit_exceeded", "en")
    assert t("rate_limit_exceeded", "uk")
    assert t("rate_limit_exceeded", "de")
