import httpx
import pytest

from app.utils import http_retry


def make_response(status_code: int = 200, headers: dict | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com")
    return httpx.Response(status_code, request=request, headers=headers or {}, json={})


class FakeClient:
    """
    Stand-in for httpx.AsyncClient whose .get()/.post() return or raise a
    sequence of pre-built outcomes, one per call — for deterministic
    retry-count and retry-condition testing without any real network call.
    Matches the real client's interface (get/post), not a generic
    request() dispatch — same shape get_with_retry/post_with_retry expect.
    """

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

    async def post(self, url, **kwargs):
        return await self._respond(url, **kwargs)


@pytest.mark.asyncio
async def test_succeeds_on_first_attempt_no_retry(mock_retry_sleep):
    client = FakeClient([make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_retries_up_to_3_times_on_5xx(mock_retry_sleep):
    client = FakeClient([make_response(500), make_response(502), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert client.call_count == 3
    assert mock_retry_sleep == [1, 1]


@pytest.mark.asyncio
async def test_exhausts_retries_and_raises_on_persistent_5xx(mock_retry_sleep):
    client = FakeClient([make_response(500), make_response(500), make_response(500)])

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert exc_info.value.response.status_code == 500
    assert client.call_count == 3
    assert mock_retry_sleep == [1, 1]


@pytest.mark.asyncio
async def test_404_fails_immediately_no_retry(mock_retry_sleep):
    client = FakeClient([make_response(404)])

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert exc_info.value.response.status_code == 404
    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_401_fails_immediately_no_retry(mock_retry_sleep):
    client = FakeClient([make_response(401)])

    with pytest.raises(httpx.HTTPStatusError):
        await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_429_uses_retry_after_header(mock_retry_sleep):
    client = FakeClient([make_response(429, headers={"Retry-After": "12"}), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert mock_retry_sleep == [12.0]


@pytest.mark.asyncio
async def test_429_falls_back_to_5s_without_retry_after_header(mock_retry_sleep):
    client = FakeClient([make_response(429), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert mock_retry_sleep == [5]


@pytest.mark.asyncio
async def test_retries_on_timeout(mock_retry_sleep):
    client = FakeClient([httpx.TimeoutException("timed out"), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert client.call_count == 2
    assert mock_retry_sleep == [1]


@pytest.mark.asyncio
async def test_retries_on_connect_error(mock_retry_sleep):
    client = FakeClient([httpx.ConnectError("connection refused"), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert client.call_count == 2


@pytest.mark.asyncio
async def test_post_with_retry_uses_post_method(mock_retry_sleep):
    client = FakeClient([make_response(200)])

    response = await http_retry.post_with_retry(client, "https://example.com", service="test")

    assert response.status_code == 200
    assert client.call_count == 1


# ── circuit breaker ────────────────────────────────────────────────────────
#
# reset_circuit_breakers() runs automatically before/after every test via the
# clear_circuit_breakers autouse fixture in conftest.py, so these tests don't
# need to call it themselves.


def _exhausted_timeout_outcomes() -> list:
    """
    3 TimeoutExceptions — exhausts one top-level get_with_retry call's own
    internal retry loop with a pure connection-level failure (no HTTPStatusError
    mixed in), the only failure shape that counts toward the breaker.
    """
    return [httpx.TimeoutException("timed out")] * http_retry.RETRY_MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_breaker_does_not_trip_on_single_exhausted_call(mock_retry_sleep):
    client = FakeClient(_exhausted_timeout_outcomes())

    with pytest.raises(httpx.TimeoutException):
        await http_retry.get_with_retry(client, "https://example.com", service="deezer")

    # One exhausted call is below BREAKER_FAILURE_THRESHOLD (3) — not open yet.
    client2 = FakeClient([make_response(200)])
    response = await http_retry.get_with_retry(client2, "https://example.com", service="deezer")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_breaker_trips_after_consecutive_exhausted_calls(mock_retry_sleep):
    service = "deezer"

    for _ in range(http_retry.BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeout_outcomes())
        with pytest.raises(httpx.TimeoutException):
            await http_retry.get_with_retry(client, "https://example.com", service=service)

    # Breaker is now open — the next call must raise immediately, without
    # touching the client at all (call_count stays 0).
    blocked_client = FakeClient([make_response(200)])
    with pytest.raises(httpx.ConnectError):
        await http_retry.get_with_retry(blocked_client, "https://example.com", service=service)

    assert blocked_client.call_count == 0


@pytest.mark.asyncio
async def test_breaker_success_resets_the_failure_counter(mock_retry_sleep):
    service = "genius"

    # 2 consecutive exhausted calls — one below the threshold of 3.
    for _ in range(http_retry.BREAKER_FAILURE_THRESHOLD - 1):
        client = FakeClient(_exhausted_timeout_outcomes())
        with pytest.raises(httpx.TimeoutException):
            await http_retry.get_with_retry(client, "https://example.com", service=service)

    # A success in between resets the counter back to 0.
    success_client = FakeClient([make_response(200)])
    await http_retry.get_with_retry(success_client, "https://example.com", service=service)

    # 2 more exhausted calls — still shouldn't trip, since the counter reset.
    for _ in range(http_retry.BREAKER_FAILURE_THRESHOLD - 1):
        client = FakeClient(_exhausted_timeout_outcomes())
        with pytest.raises(httpx.TimeoutException):
            await http_retry.get_with_retry(client, "https://example.com", service=service)

    still_open_check = FakeClient([make_response(200)])
    response = await http_retry.get_with_retry(
        still_open_check, "https://example.com", service=service
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_breaker_cooldown_expires_and_allows_retry(mock_retry_sleep, monkeypatch):
    service = "spotify"

    for _ in range(http_retry.BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeout_outcomes())
        with pytest.raises(httpx.TimeoutException):
            await http_retry.get_with_retry(client, "https://example.com", service=service)

    # Simulate the cooldown window having already passed.
    import time as time_module

    real_time = time_module.time
    monkeypatch.setattr(time_module, "time", lambda: real_time() + 3600)

    client_after_cooldown = FakeClient([make_response(200)])
    response = await http_retry.get_with_retry(
        client_after_cooldown, "https://example.com", service=service
    )

    assert response.status_code == 200
    assert client_after_cooldown.call_count == 1


@pytest.mark.asyncio
async def test_breaker_state_does_not_bleed_across_services(mock_retry_sleep):
    """
    Deezer being down must not block Spotify — breaker state is per-service.
    """
    for _ in range(http_retry.BREAKER_FAILURE_THRESHOLD):
        client = FakeClient(_exhausted_timeout_outcomes())
        with pytest.raises(httpx.TimeoutException):
            await http_retry.get_with_retry(client, "https://example.com", service="deezer")

    deezer_check = FakeClient([make_response(200)])
    with pytest.raises(httpx.ConnectError):
        await http_retry.get_with_retry(deezer_check, "https://example.com", service="deezer")

    spotify_client = FakeClient([make_response(200)])
    response = await http_retry.get_with_retry(
        spotify_client, "https://example.com", service="spotify"
    )
    assert response.status_code == 200
    assert spotify_client.call_count == 1
