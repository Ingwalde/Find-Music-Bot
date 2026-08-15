import json

import pytest
from redis.exceptions import RedisError

from app.services import search_cache_service
from tests.conftest import to_async


class FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.fail = fail

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise RedisError("connection lost")
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        if self.fail:
            raise RedisError("connection lost")
        self.store[key] = value
        self.ttls[key] = ttl


def make_tracks():
    return [
        {"deezer_track_id": "1", "title": "SOS", "artist": "ABBA"},
        {"deezer_track_id": "2", "title": "Waterloo", "artist": "ABBA"},
    ]


@pytest.fixture
def wired(monkeypatch):
    """
    Wires the service with a fake Redis and recording stubs for the PostgreSQL
    tier and the Deezer call, so each test can assert which tier answered.
    """
    calls: dict = {"deezer": 0, "pg_read": 0, "pg_write": 0}
    client = FakeRedis()

    monkeypatch.setattr(search_cache_service, "get_redis_client", lambda: client)

    def pg_read(query, source):
        calls["pg_read"] += 1
        return calls.get("pg_value")

    def pg_write(query, source, results):
        calls["pg_write"] += 1

    def deezer(query, limit):
        calls["deezer"] += 1
        return make_tracks()

    monkeypatch.setattr(search_cache_service, "get_cached_search", to_async(pg_read))
    monkeypatch.setattr(search_cache_service, "save_search_cache", to_async(pg_write))
    monkeypatch.setattr(search_cache_service, "search_tracks", to_async(deezer))

    return client, calls


@pytest.mark.asyncio
async def test_redis_hit_skips_postgres_and_deezer(wired):
    client, calls = wired
    tracks = make_tracks()
    client.store["searchcache:deezer:abba"] = json.dumps(tracks)

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == tracks
    assert calls["pg_read"] == 0
    assert calls["deezer"] == 0


@pytest.mark.asyncio
async def test_postgres_hit_warms_redis(wired):
    client, calls = wired
    calls["pg_value"] = make_tracks()

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == make_tracks()
    assert calls["deezer"] == 0
    assert "searchcache:deezer:abba" in client.store


@pytest.mark.asyncio
async def test_full_miss_calls_deezer_and_writes_both_tiers(wired):
    client, calls = wired
    calls["pg_value"] = None

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == make_tracks()
    assert calls["deezer"] == 1
    assert calls["pg_write"] == 1
    assert "searchcache:deezer:abba" in client.store


@pytest.mark.asyncio
async def test_redis_write_uses_the_24h_ttl(wired):
    client, calls = wired
    calls["pg_value"] = None

    await search_cache_service.search_tracks_cached("ABBA", limit=10)

    key = "searchcache:deezer:abba"
    assert client.ttls[key] == search_cache_service.SEARCH_CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_unreadable_redis_payload_falls_through_to_postgres(wired):
    client, calls = wired
    client.store["searchcache:deezer:abba"] = "{not json"
    calls["pg_value"] = make_tracks()

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == make_tracks()
    assert calls["pg_read"] == 1


@pytest.mark.asyncio
async def test_non_list_redis_payload_falls_through_to_postgres(wired):
    client, calls = wired
    client.store["searchcache:deezer:abba"] = json.dumps({"not": "a list"})
    calls["pg_value"] = make_tracks()

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == make_tracks()
    assert calls["pg_read"] == 1


@pytest.mark.asyncio
async def test_redis_outage_still_serves_from_postgres(monkeypatch):
    """The reason the PostgreSQL tier was kept: Redis down is not a cold cache."""
    calls = {"pg_read": 0, "deezer": 0}
    monkeypatch.setattr(search_cache_service, "get_redis_client", lambda: FakeRedis(fail=True))

    def pg_read(query, source):
        calls["pg_read"] += 1
        return make_tracks()

    def deezer(query, limit):
        calls["deezer"] += 1
        return []

    monkeypatch.setattr(search_cache_service, "get_cached_search", to_async(pg_read))
    monkeypatch.setattr(search_cache_service, "save_search_cache", to_async(lambda q, s, r: None))
    monkeypatch.setattr(search_cache_service, "search_tracks", to_async(deezer))

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == make_tracks()
    assert calls["pg_read"] == 1
    assert calls["deezer"] == 0


@pytest.mark.asyncio
async def test_empty_deezer_result_is_not_cached(wired, monkeypatch):
    client, calls = wired
    calls["pg_value"] = None
    monkeypatch.setattr(search_cache_service, "search_tracks", to_async(lambda query, limit: []))

    result = await search_cache_service.search_tracks_cached("nothing", limit=10)

    assert result == []
    assert "searchcache:deezer:nothing" not in client.store
