import asyncio
import time

import httpx

from app.config.settings import settings
from app.utils.metrics import (
    circuit_breaker_open,
    external_api_latency_seconds,
    external_api_requests_total,
)

RETRY_MAX_ATTEMPTS = 3
RETRY_FIXED_PAUSE_SECONDS = 1
RETRY_429_FALLBACK_PAUSE_SECONDS = 5

# Circuit breaker for network-level outages (timeout/connect failures only —
# not HTTP 4xx/5xx, which are already handled per-request above). Orthogonal
# to Spotify's own 403 access-restriction cooldown in platforms/spotify/auth.py;
# this covers "is the service reachable at all" for any of the three services
# that route through get_with_retry/post_with_retry.
BREAKER_FAILURE_THRESHOLD = 3
BREAKER_TRANSIENT_ERRORS = (httpx.TimeoutException, httpx.ConnectError)

_breaker_lock = asyncio.Lock()
_breaker_failure_counts: dict[str, int] = {}
_breaker_blocked_until: dict[str, float] = {}
# Half-open: after cooldown expires exactly one probe request is allowed.
# While that probe is in flight, all other callers see the breaker as open.
_breaker_probe_in_progress: dict[str, bool] = {}


def reset_circuit_breakers() -> None:
    """
    Resets all per-service circuit breaker state. Used by tests.
    """
    _breaker_failure_counts.clear()
    _breaker_blocked_until.clear()
    _breaker_probe_in_progress.clear()
    for service in list(circuit_breaker_open._metrics.keys()):
        circuit_breaker_open.labels(service=service[0]).set(0)


async def _check_breaker(service: str) -> bool:
    """
    Raises immediately if the breaker is open or a probe is already in flight.
    Returns True if this call is the half-open probe (caller must clear the
    probe flag in a finally block regardless of outcome).
    """
    async with _breaker_lock:
        blocked_until = _breaker_blocked_until.get(service, 0.0)

        if blocked_until == 0.0:
            return False  # breaker closed — normal operation

        if time.time() < blocked_until:
            # Still in cooldown — open
            raise httpx.ConnectError(
                f"{service}: circuit breaker open, skipping request until cooldown expires"
            )

        # Cooldown expired — half-open state.
        if _breaker_probe_in_progress.get(service, False):
            # Another probe is already in flight — treat as open to avoid
            # thundering herd while the probe result is still unknown.
            raise httpx.ConnectError(
                f"{service}: circuit breaker half-open, probe in progress"
            )

        # This caller wins the probe slot.
        _breaker_probe_in_progress[service] = True
        return True


async def _clear_probe(service: str) -> None:
    async with _breaker_lock:
        _breaker_probe_in_progress.pop(service, None)


async def _record_breaker_outcome(service: str, *, failed: bool) -> None:
    """
    A single top-level get_with_retry/post_with_retry call counts as one
    outcome here, regardless of how many of its own internal retry attempts
    it took — tripping requires BREAKER_FAILURE_THRESHOLD consecutive fully-
    exhausted calls, not individual attempts within one call, so a single
    call that recovers on its own second attempt never counts as a failure.

    On success the breaker is fully closed (blocked_until cleared) so that
    the next check sees a clean state rather than re-entering half-open.
    """
    async with _breaker_lock:
        if not failed:
            _breaker_failure_counts[service] = 0
            _breaker_blocked_until.pop(service, None)
            circuit_breaker_open.labels(service=service).set(0)
            return

        count = _breaker_failure_counts.get(service, 0) + 1
        _breaker_failure_counts[service] = count

        if count >= BREAKER_FAILURE_THRESHOLD:
            _breaker_blocked_until[service] = (
                time.time() + settings.EXTERNAL_SERVICE_COOLDOWN_SECONDS
            )
            circuit_breaker_open.labels(service=service).set(1)


async def _request_with_retry(request_fn, url: str, *, service: str, **kwargs) -> httpx.Response:
    """
    Calls request_fn(url, **kwargs) with up to 3 attempts. request_fn is a
    bound client method (client.get or client.post) rather than a generic
    client.request(method, ...) dispatch, so this works with both the real
    httpx.AsyncClient and every existing FakeAsyncClient test double, which
    only implement get()/post().

    Retries on transient errors only: timeout, connection error, HTTP 5xx,
    HTTP 429. Fails immediately on any other 4xx (e.g. 404) — a client
    error will not succeed on retry, so retrying just wastes time.

    429 is a special case: a fixed 1s pause is too short against an API's
    own rate limit, so 3 quick retries would just hammer it again. Uses
    the Retry-After header when the API provides one, else a 5s fallback.

    service identifies which circuit breaker bucket this call belongs to
    (e.g. "spotify", "deezer", "genius"). Checked before the first attempt;
    if that service's breaker is open, this raises immediately with no
    network call.
    """
    is_probe = await _check_breaker(service)

    last_error: Exception | None = None
    start = time.monotonic()

    try:
        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                response = await request_fn(url, **kwargs)
                response.raise_for_status()
                await _record_breaker_outcome(service, failed=False)
                external_api_requests_total.labels(service=service, outcome="success").inc()
                external_api_latency_seconds.labels(service=service).observe(
                    time.monotonic() - start
                )
                return response
            except httpx.HTTPStatusError as error:
                status = error.response.status_code

                if status == 429:
                    retry_after = error.response.headers.get("Retry-After")
                    pause = (
                        float(retry_after) if retry_after else RETRY_429_FALLBACK_PAUSE_SECONDS
                    )
                elif 500 <= status < 600:
                    pause = RETRY_FIXED_PAUSE_SECONDS
                else:
                    external_api_requests_total.labels(service=service, outcome="error").inc()
                    raise

                last_error = error
            except BREAKER_TRANSIENT_ERRORS as error:
                pause = RETRY_FIXED_PAUSE_SECONDS
                last_error = error

            if attempt < RETRY_MAX_ATTEMPTS - 1:
                await asyncio.sleep(pause)

        if isinstance(last_error, BREAKER_TRANSIENT_ERRORS):
            await _record_breaker_outcome(service, failed=True)

        external_api_requests_total.labels(service=service, outcome="error").inc()
        external_api_latency_seconds.labels(service=service).observe(time.monotonic() - start)
        raise last_error
    finally:
        if is_probe:
            await _clear_probe(service)


async def get_with_retry(
    client: httpx.AsyncClient, url: str, *, service: str, **kwargs
) -> httpx.Response:
    return await _request_with_retry(client.get, url, service=service, **kwargs)


async def post_with_retry(
    client: httpx.AsyncClient, url: str, *, service: str, **kwargs
) -> httpx.Response:
    return await _request_with_retry(client.post, url, service=service, **kwargs)
