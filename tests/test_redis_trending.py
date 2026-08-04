"""
Redis-backed trending cache tests.
Requires the test-redis compose service: docker compose up -d test-redis
Set REDIS_URL=redis://localhost:6380 before running.
"""
import json

import pytest

from app.services.recommendations_service import (
    _TRENDING_REDIS_KEY,
    get_cached_trending,
    invalidate_trending_cache,
)


def _make_tracks(n: int) -> list[dict]:
    return [{"deezer_track_id": str(i), "title": f"Track {i}", "artist": "ABBA"} for i in range(n)]


@pytest.mark.asyncio
async def test_redis_trending_cache_miss_calls_fetch_fn(live_redis):
    called = []

    async def fetch_fn(limit):
        called.append(limit)
        return _make_tracks(limit)

    result = await get_cached_trending(fetch_fn, limit=3)

    assert called == [3]
    assert len(result) == 3


@pytest.mark.asyncio
async def test_redis_trending_cache_hit_skips_fetch_fn(live_redis):
    tracks = _make_tracks(3)
    await live_redis.set(_TRENDING_REDIS_KEY, json.dumps(tracks), ex=3600)

    called = []

    async def fetch_fn(limit):
        called.append(limit)
        return []

    result = await get_cached_trending(fetch_fn, limit=3)

    assert called == []
    assert result == tracks


@pytest.mark.asyncio
async def test_redis_trending_cache_stores_after_fetch(live_redis):
    async def fetch_fn(limit):
        return _make_tracks(limit)

    await get_cached_trending(fetch_fn, limit=2)

    raw = await live_redis.get(_TRENDING_REDIS_KEY)
    assert raw is not None
    stored = json.loads(raw)
    assert len(stored) == 2


@pytest.mark.asyncio
async def test_redis_trending_cache_fallback_on_broken_client(monkeypatch):
    """When Redis raises, falls back to in-memory cache."""
    import app.services.redis_client as redis_client_module

    class BrokenClient:
        async def get(self, key):
            raise ConnectionError("Redis down")

        async def setex(self, *args):
            raise ConnectionError("Redis down")

    monkeypatch.setattr(redis_client_module, "_client", BrokenClient())
    invalidate_trending_cache()

    async def fetch_fn(limit):
        return _make_tracks(limit)

    result = await get_cached_trending(fetch_fn, limit=2)
    assert len(result) == 2
