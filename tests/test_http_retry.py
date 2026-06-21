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

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_retries_up_to_3_times_on_5xx(mock_retry_sleep):
    client = FakeClient([make_response(500), make_response(502), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert client.call_count == 3
    assert mock_retry_sleep == [1, 1]


@pytest.mark.asyncio
async def test_exhausts_retries_and_raises_on_persistent_5xx(mock_retry_sleep):
    client = FakeClient([make_response(500), make_response(500), make_response(500)])

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await http_retry.get_with_retry(client, "https://example.com")

    assert exc_info.value.response.status_code == 500
    assert client.call_count == 3
    assert mock_retry_sleep == [1, 1]


@pytest.mark.asyncio
async def test_404_fails_immediately_no_retry(mock_retry_sleep):
    client = FakeClient([make_response(404)])

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await http_retry.get_with_retry(client, "https://example.com")

    assert exc_info.value.response.status_code == 404
    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_401_fails_immediately_no_retry(mock_retry_sleep):
    client = FakeClient([make_response(401)])

    with pytest.raises(httpx.HTTPStatusError):
        await http_retry.get_with_retry(client, "https://example.com")

    assert client.call_count == 1
    assert mock_retry_sleep == []


@pytest.mark.asyncio
async def test_429_uses_retry_after_header(mock_retry_sleep):
    client = FakeClient([make_response(429, headers={"Retry-After": "12"}), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert mock_retry_sleep == [12.0]


@pytest.mark.asyncio
async def test_429_falls_back_to_5s_without_retry_after_header(mock_retry_sleep):
    client = FakeClient([make_response(429), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert mock_retry_sleep == [5]


@pytest.mark.asyncio
async def test_retries_on_timeout(mock_retry_sleep):
    client = FakeClient([httpx.TimeoutException("timed out"), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert client.call_count == 2
    assert mock_retry_sleep == [1]


@pytest.mark.asyncio
async def test_retries_on_connect_error(mock_retry_sleep):
    client = FakeClient([httpx.ConnectError("connection refused"), make_response(200)])

    response = await http_retry.get_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert client.call_count == 2


@pytest.mark.asyncio
async def test_post_with_retry_uses_post_method(mock_retry_sleep):
    client = FakeClient([make_response(200)])

    response = await http_retry.post_with_retry(client, "https://example.com")

    assert response.status_code == 200
    assert client.call_count == 1
