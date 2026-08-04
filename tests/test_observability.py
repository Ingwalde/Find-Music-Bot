"""
Tests for v3.4.0 observability features:
- JSON logging formatter
- Correlation ID context variable
- Prometheus /metrics endpoint
- Search cache hit/miss counters
"""
import json
import logging

import pytest
from fastapi.testclient import TestClient

import app.monitoring as monitoring
from app.utils.correlation import get_correlation_id, new_correlation_id, set_correlation_id
from app.utils.logger import _JsonFormatter

# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


def test_json_formatter_emits_valid_json():
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello world",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "hello world"
    assert parsed["logger"] == "test.logger"
    assert "ts" in parsed


def test_json_formatter_includes_correlation_id_when_set():
    set_correlation_id("abc123")
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="msg",
        args=(),
        exc_info=None,
    )
    record.correlation_id = get_correlation_id()
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["correlation_id"] == "abc123"


def test_json_formatter_omits_correlation_id_when_absent():
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="warn",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "correlation_id" not in parsed


# ---------------------------------------------------------------------------
# Correlation ID
# ---------------------------------------------------------------------------


def test_correlation_id_set_and_get():
    set_correlation_id("testid")
    assert get_correlation_id() == "testid"


def test_new_correlation_id_is_12_hex_chars():
    cid = new_correlation_id()
    assert len(cid) == 12
    assert all(c in "0123456789abcdef" for c in cid)


def test_correlation_id_default_is_none():
    import contextvars

    ctx = contextvars.copy_context()

    def _check():
        from app.utils import correlation
        correlation._correlation_id.set(None)
        return get_correlation_id()

    result = ctx.run(_check)
    assert result is None


# ---------------------------------------------------------------------------
# Prometheus /metrics endpoint
# ---------------------------------------------------------------------------


def test_metrics_endpoint_returns_200():
    client = TestClient(monitoring.create_app())
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_content_type_is_prometheus():
    client = TestClient(monitoring.create_app())
    response = client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


def test_metrics_endpoint_contains_bot_metrics():
    client = TestClient(monitoring.create_app())
    response = client.get("/metrics")
    body = response.text
    assert "bot_external_api_requests_total" in body
    assert "bot_search_cache_hits_total" in body
    assert "bot_search_cache_misses_total" in body
    assert "bot_circuit_breaker_open" in body


# ---------------------------------------------------------------------------
# Search cache counters (unit — no DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_cache_hit_counter_increments(monkeypatch):
    import app.services.search_cache_service as svc
    from app.utils import metrics

    before = _get_counter_value(metrics.search_cache_hits_total)

    async def fake_get_cached(query, source):
        return [{"title": "cached"}]

    monkeypatch.setattr(svc, "get_cached_search", fake_get_cached)
    await svc.search_tracks_cached("test query", limit=5)

    after = _get_counter_value(metrics.search_cache_hits_total)
    assert after == before + 1


@pytest.mark.asyncio
async def test_search_cache_miss_counter_increments(monkeypatch):
    import app.services.search_cache_service as svc
    from app.utils import metrics

    before = _get_counter_value(metrics.search_cache_misses_total)

    async def fake_get_cached(query, source):
        return None

    async def fake_search_tracks(query, limit):
        return []

    monkeypatch.setattr(svc, "get_cached_search", fake_get_cached)
    monkeypatch.setattr(svc, "search_tracks", fake_search_tracks)
    await svc.search_tracks_cached("miss query", limit=5)

    after = _get_counter_value(metrics.search_cache_misses_total)
    assert after == before + 1


def _get_counter_value(counter) -> float:
    try:
        return counter._value.get()
    except Exception:
        return 0.0
