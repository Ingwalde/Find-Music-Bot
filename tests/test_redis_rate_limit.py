"""
Redis-backed rate limit and warn-once tests.
Requires the test-redis compose service: docker compose up -d test-redis
Set REDIS_URL=redis://localhost:6380 before running.
"""
import pytest

from app.bot import rate_limit
from app.config.settings import settings


@pytest.mark.asyncio
async def test_redis_allows_up_to_max_requests(live_redis):
    for _ in range(settings.RATE_LIMIT_MAX_REQUESTS):
        assert await rate_limit.check_rate_limit(10) is True


@pytest.mark.asyncio
async def test_redis_blocks_at_max_requests(live_redis):
    for _ in range(settings.RATE_LIMIT_MAX_REQUESTS):
        await rate_limit.check_rate_limit(10)

    assert await rate_limit.check_rate_limit(10) is False


@pytest.mark.asyncio
async def test_redis_rate_limit_is_per_user(live_redis):
    for _ in range(settings.RATE_LIMIT_MAX_REQUESTS):
        await rate_limit.check_rate_limit(10)

    assert await rate_limit.check_rate_limit(10) is False
    assert await rate_limit.check_rate_limit(11) is True


@pytest.mark.asyncio
async def test_redis_admin_always_allowed(live_redis):
    for _ in range(25):
        assert await rate_limit.check_rate_limit(10, is_admin=True) is True


@pytest.mark.asyncio
async def test_redis_warn_once_true_first_time(live_redis):
    assert await rate_limit.should_warn_once(20) is True


@pytest.mark.asyncio
async def test_redis_warn_once_false_on_repeat(live_redis):
    await rate_limit.should_warn_once(20)
    assert await rate_limit.should_warn_once(20) is False


@pytest.mark.asyncio
async def test_redis_warn_flag_cleared_on_successful_request(live_redis):
    await rate_limit.should_warn_once(20)

    # Successful request should clear the warn flag
    assert await rate_limit.check_rate_limit(20) is True

    # Now warn flag should be gone — next warn returns True again
    assert await rate_limit.should_warn_once(20) is True


@pytest.mark.asyncio
async def test_redis_fallback_on_unavailable_client(monkeypatch):
    """When Redis client raises, falls back to in-memory."""
    import app.services.redis_client as redis_client_module

    class BrokenClient:
        def pipeline(self):
            raise ConnectionError("Redis down")

    monkeypatch.setattr(redis_client_module, "_client", BrokenClient())

    # Should not raise; falls back to in-memory
    result = await rate_limit.check_rate_limit(30)
    assert result is True
