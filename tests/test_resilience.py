"""
Tests for v3.4.1 resilience features:
- Breaker half-open: probe-wins / probe-in-flight blocks / probe-fail re-trips
- Graceful drain: counter tracks in-flight handlers, drain waits for zero
"""
import asyncio
import time as time_module

import httpx
import pytest

from app.utils import http_retry
from app.utils.http_retry import (
    BREAKER_FAILURE_THRESHOLD,
    get_with_retry,
    reset_circuit_breakers,
)


def make_response(status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com")
    return httpx.Response(status_code, request=request, json={})


def _exhausted_timeouts():
    return [httpx.TimeoutException("t")] * 3


class FakeClient:
    def __init__(self, outcomes: list):
        self._outcomes = list(outcomes)
        self.call_count = 0

    async def _respond(self, url, **kwargs):
        self.call_count += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def get(self, url, **kwargs):
        return await self._respond(url, **kwargs)


@pytest.fixture(autouse=True)
def clean_breaker():
    reset_circuit_breakers()
    yield
    reset_circuit_breakers()


@pytest.fixture
def mock_retry_sleep(monkeypatch):
    async def _no_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)


# ---------------------------------------------------------------------------
# Half-open: probe wins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_half_open_probe_succeeds_closes_breaker(mock_retry_sleep, monkeypatch):
    service = "deezer"

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeouts())
        with pytest.raises(httpx.TimeoutException):
            await get_with_retry(client, "https://x.com", service=service)

    real_time = time_module.time
    monkeypatch.setattr(time_module, "time", lambda: real_time() + 9999)

    probe_client = FakeClient([make_response(200)])
    resp = await get_with_retry(probe_client, "https://x.com", service=service)
    assert resp.status_code == 200

    # Breaker fully closed — next call goes through with real time.
    monkeypatch.setattr(time_module, "time", real_time)
    normal_client = FakeClient([make_response(200)])
    resp2 = await get_with_retry(normal_client, "https://x.com", service=service)
    assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# Half-open: concurrent callers blocked while probe in flight
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_half_open_blocks_concurrent_callers_while_probe_in_flight(
    mock_retry_sleep, monkeypatch
):
    service = "genius"

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeouts())
        with pytest.raises(httpx.TimeoutException):
            await get_with_retry(client, "https://x.com", service=service)

    real_time = time_module.time
    monkeypatch.setattr(time_module, "time", lambda: real_time() + 9999)

    # Simulate probe already in flight.
    http_retry._breaker_probe_in_progress[service] = True

    blocked_client = FakeClient([make_response(200)])
    with pytest.raises(httpx.ConnectError, match="probe in progress"):
        await get_with_retry(blocked_client, "https://x.com", service=service)
    assert blocked_client.call_count == 0


# ---------------------------------------------------------------------------
# Half-open: probe fails → trips again
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_half_open_probe_failure_re_trips_breaker(mock_retry_sleep, monkeypatch):
    service = "spotify"

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeouts())
        with pytest.raises(httpx.TimeoutException):
            await get_with_retry(client, "https://x.com", service=service)

    real_time = time_module.time
    monkeypatch.setattr(time_module, "time", lambda: real_time() + 9999)

    failing_probe = FakeClient(_exhausted_timeouts())
    with pytest.raises(httpx.TimeoutException):
        await get_with_retry(failing_probe, "https://x.com", service=service)

    # Probe flag cleared after failure.
    assert not http_retry._breaker_probe_in_progress.get(service, False)
    # Breaker open again.
    assert service in http_retry._breaker_blocked_until


# ---------------------------------------------------------------------------
# Graceful drain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_drain_returns_immediately_when_no_handlers_in_flight():
    import app.bot.shutdown_middleware as sm
    from app.bot.shutdown_middleware import drain_handlers

    sm._in_flight = 0
    await drain_handlers(timeout=5.0)


@pytest.mark.asyncio
async def test_drain_waits_for_in_flight_handler_to_finish():
    import app.bot.shutdown_middleware as sm
    from app.bot.shutdown_middleware import drain_handlers

    sm._in_flight = 1

    async def finish_after_tick():
        await asyncio.sleep(0)  # yield once so drain can start, then complete
        sm._in_flight = 0

    task = asyncio.create_task(finish_after_tick())
    await drain_handlers(timeout=2.0)
    await task
    assert sm._in_flight == 0


@pytest.mark.asyncio
async def test_drain_times_out_and_returns_when_handlers_stuck():
    import app.bot.shutdown_middleware as sm
    from app.bot.shutdown_middleware import drain_handlers

    sm._in_flight = 1
    try:
        await asyncio.wait_for(drain_handlers(timeout=0.1), timeout=1.0)
    finally:
        sm._in_flight = 0


# ---------------------------------------------------------------------------
# Concurrency: only one probe wins when multiple callers race
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_check_breaker_only_one_probe_wins():
    """N concurrent callers in half-open state: exactly one gets the probe slot."""
    service = "race_probe"

    # Expired cooldown → half-open
    http_retry._breaker_blocked_until[service] = time_module.time() - 1

    results = []

    async def call_check():
        try:
            is_probe = await http_retry._check_breaker(service)
            results.append("probe" if is_probe else "closed")
        except Exception:
            results.append("blocked")

    await asyncio.gather(*[call_check() for _ in range(8)])

    assert results.count("probe") == 1
    assert results.count("blocked") == 7


# ---------------------------------------------------------------------------
# Partial-failure: only transient network errors trip the breaker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_failure_4xx_does_not_trip_breaker(mock_retry_sleep):
    service = "partial_4xx"
    request = httpx.Request("GET", "https://x.com")

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        err = httpx.HTTPStatusError("404", request=request, response=make_response(404))
        with pytest.raises(httpx.HTTPStatusError):
            await get_with_retry(FakeClient([err]), "https://x.com", service=service)

    assert service not in http_retry._breaker_blocked_until


@pytest.mark.asyncio
async def test_partial_failure_5xx_exhausted_does_not_trip_breaker(mock_retry_sleep):
    service = "partial_5xx"
    request = httpx.Request("GET", "https://x.com")

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        err = httpx.HTTPStatusError("503", request=request, response=make_response(503))
        with pytest.raises(httpx.HTTPStatusError):
            await get_with_retry(FakeClient([err] * 3), "https://x.com", service=service)

    assert service not in http_retry._breaker_blocked_until
