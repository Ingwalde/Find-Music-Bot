import asyncio

import httpx

RETRY_MAX_ATTEMPTS = 3
RETRY_FIXED_PAUSE_SECONDS = 1
RETRY_429_FALLBACK_PAUSE_SECONDS = 5


async def _request_with_retry(request_fn, url: str, **kwargs) -> httpx.Response:
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
    """
    last_error: Exception | None = None

    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            response = await request_fn(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as error:
            status = error.response.status_code

            if status == 429:
                retry_after = error.response.headers.get("Retry-After")
                pause = float(retry_after) if retry_after else RETRY_429_FALLBACK_PAUSE_SECONDS
            elif 500 <= status < 600:
                pause = RETRY_FIXED_PAUSE_SECONDS
            else:
                raise

            last_error = error
        except (httpx.TimeoutException, httpx.ConnectError) as error:
            pause = RETRY_FIXED_PAUSE_SECONDS
            last_error = error

        if attempt < RETRY_MAX_ATTEMPTS - 1:
            await asyncio.sleep(pause)

    raise last_error


async def get_with_retry(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    return await _request_with_retry(client.get, url, **kwargs)


async def post_with_retry(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    return await _request_with_retry(client.post, url, **kwargs)
