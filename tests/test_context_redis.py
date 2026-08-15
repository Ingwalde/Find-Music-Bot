import json

import pytest
from redis.exceptions import RedisError

from app.bot import context


class FakeRedis:
    """
    Minimal Redis stand-in covering only the get/setex pair context.py uses.
    TTL is recorded but not enforced — Redis handles expiry itself, so the
    module deliberately has no TTL check on the Redis path.
    """

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


def make_tracks(count: int) -> list[dict]:
    return [{"deezer_track_id": str(index), "title": f"Track {index}"} for index in range(count)]


@pytest.fixture
def fake_redis(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(context, "get_redis_client", lambda: client)
    return client


@pytest.mark.asyncio
async def test_save_writes_to_redis_not_memory(fake_redis):
    context.search_contexts.clear()

    await context.save_search_context(user_id=7, query="abba", tracks=make_tracks(3))

    assert "sc:7" in fake_redis.store
    assert 7 not in context.search_contexts


@pytest.mark.asyncio
async def test_save_applies_the_shared_ttl(fake_redis):
    await context.save_search_context(user_id=7, query="abba", tracks=make_tracks(1))

    assert fake_redis.ttls["sc:7"] == context.SEARCH_CONTEXT_TTL_SECONDS


@pytest.mark.asyncio
async def test_context_survives_an_in_memory_wipe(fake_redis):
    """The point of the Redis tier: pagination outlives a bot restart."""
    tracks = make_tracks(4)
    await context.save_search_context(user_id=7, query="abba", tracks=tracks)

    context.search_contexts.clear()

    stored = await context.get_search_context(7)

    assert stored is not None
    assert stored["query"] == "abba"
    assert stored["tracks"] == tracks


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_user(fake_redis):
    assert await context.get_search_context(999) is None


@pytest.mark.asyncio
async def test_unreadable_payload_is_discarded_not_raised(fake_redis):
    fake_redis.store["sc:7"] = "{not json"

    assert await context.get_search_context(7) is None


@pytest.mark.asyncio
async def test_non_dict_payload_is_rejected(fake_redis):
    fake_redis.store["sc:7"] = json.dumps(["not", "a", "dict"])

    assert await context.get_search_context(7) is None


@pytest.mark.asyncio
async def test_set_search_page_persists_through_redis(fake_redis):
    await context.save_search_context(user_id=7, query="abba", tracks=make_tracks(10))

    normalized = await context.set_search_page(user_id=7, page=1, page_size=5)

    assert normalized == 1
    assert await context.get_current_page(7) == 1


@pytest.mark.asyncio
async def test_set_search_page_clamps_beyond_last_page(fake_redis):
    await context.save_search_context(user_id=7, query="abba", tracks=make_tracks(10))

    assert await context.set_search_page(user_id=7, page=99, page_size=5) == 1


@pytest.mark.asyncio
async def test_set_search_page_returns_zero_without_a_context(fake_redis):
    assert await context.set_search_page(user_id=404, page=2, page_size=5) == 0


@pytest.mark.asyncio
async def test_page_tracks_slice_comes_from_redis(fake_redis):
    tracks = make_tracks(10)
    await context.save_search_context(user_id=7, query="abba", tracks=tracks)
    context.search_contexts.clear()

    page_two = await context.get_page_tracks(user_id=7, page_size=5, page=1)

    assert page_two == tracks[5:10]


@pytest.mark.asyncio
async def test_total_pages_comes_from_redis(fake_redis):
    await context.save_search_context(user_id=7, query="abba", tracks=make_tracks(12))
    context.search_contexts.clear()

    assert await context.get_total_pages(user_id=7, page_size=5) == 3


@pytest.mark.asyncio
async def test_save_falls_back_to_memory_when_redis_errors(monkeypatch):
    context.search_contexts.clear()
    monkeypatch.setattr(context, "get_redis_client", lambda: FakeRedis(fail=True))

    await context.save_search_context(user_id=8, query="abba", tracks=make_tracks(2))

    assert 8 in context.search_contexts


@pytest.mark.asyncio
async def test_get_falls_back_to_memory_when_redis_errors(monkeypatch):
    context.search_contexts.clear()
    monkeypatch.setattr(context, "get_redis_client", lambda: FakeRedis(fail=True))

    await context.save_search_context(user_id=8, query="abba", tracks=make_tracks(2))
    stored = await context.get_search_context(8)

    assert stored is not None
    assert stored["query"] == "abba"


@pytest.mark.asyncio
async def test_set_search_page_falls_back_to_memory_when_redis_errors(monkeypatch):
    context.search_contexts.clear()
    monkeypatch.setattr(context, "get_redis_client", lambda: FakeRedis(fail=True))

    await context.save_search_context(user_id=8, query="abba", tracks=make_tracks(10))

    assert await context.set_search_page(user_id=8, page=1, page_size=5) == 1
