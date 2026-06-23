import pytest

from app.services import search_cache_service
from tests.conftest import to_async


def make_tracks():
    return [
        {"deezer_track_id": "1", "title": "SOS", "artist": "ABBA"},
        {"deezer_track_id": "2", "title": "Waterloo", "artist": "ABBA"},
    ]


def test_normalize_query_lowercases_and_trims():
    assert search_cache_service.normalize_query("  Beatles  ") == "beatles"
    assert search_cache_service.normalize_query("BEATLES") == "beatles"
    assert search_cache_service.normalize_query("beatles") == "beatles"


@pytest.mark.asyncio
async def test_cache_hit_skips_the_api_call(monkeypatch):
    tracks = make_tracks()
    called = {}
    monkeypatch.setattr(
        search_cache_service, "get_cached_search", to_async(lambda q, s: tracks)
    )
    monkeypatch.setattr(
        search_cache_service,
        "search_tracks",
        to_async(lambda query, limit: called.update(called=True)),
    )
    monkeypatch.setattr(
        search_cache_service, "save_search_cache", to_async(lambda q, s, r: called.update(saved=True))
    )

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == tracks
    assert "called" not in called
    assert "saved" not in called


@pytest.mark.asyncio
async def test_cache_miss_calls_api_and_writes_result(monkeypatch):
    tracks = make_tracks()
    saved = {}
    monkeypatch.setattr(search_cache_service, "get_cached_search", to_async(lambda q, s: None))
    monkeypatch.setattr(
        search_cache_service, "search_tracks", to_async(lambda query, limit: tracks)
    )
    monkeypatch.setattr(
        search_cache_service,
        "save_search_cache",
        to_async(lambda q, s, r: saved.update(query=q, source=s, results=r)),
    )

    result = await search_cache_service.search_tracks_cached("ABBA", limit=10)

    assert result == tracks
    assert saved == {"query": "abba", "source": "deezer", "results": tracks}


@pytest.mark.asyncio
async def test_cache_miss_with_empty_api_result_does_not_write_cache(monkeypatch):
    saved = {}
    monkeypatch.setattr(search_cache_service, "get_cached_search", to_async(lambda q, s: None))
    monkeypatch.setattr(search_cache_service, "search_tracks", to_async(lambda query, limit: []))
    monkeypatch.setattr(
        search_cache_service, "save_search_cache", to_async(lambda q, s, r: saved.update(called=True))
    )

    result = await search_cache_service.search_tracks_cached("nonexistent", limit=10)

    assert result == []
    assert "called" not in saved


@pytest.mark.asyncio
async def test_normalization_makes_different_casing_hit_the_same_cache_key(monkeypatch):
    lookups = []
    monkeypatch.setattr(
        search_cache_service,
        "get_cached_search",
        to_async(lambda q, s: lookups.append(q) or None),
    )
    monkeypatch.setattr(search_cache_service, "search_tracks", to_async(lambda query, limit: []))
    monkeypatch.setattr(search_cache_service, "save_search_cache", to_async(lambda q, s, r: None))

    await search_cache_service.search_tracks_cached("Beatles", limit=10)
    await search_cache_service.search_tracks_cached("beatles ", limit=10)
    await search_cache_service.search_tracks_cached("  BEATLES", limit=10)

    assert lookups == ["beatles", "beatles", "beatles"]


@pytest.mark.asyncio
async def test_deezer_query_text_is_sent_unnormalized(monkeypatch):
    """The cache KEY is normalized; the actual API call still gets the original text."""
    sent_queries = []
    monkeypatch.setattr(search_cache_service, "get_cached_search", to_async(lambda q, s: None))
    monkeypatch.setattr(
        search_cache_service,
        "search_tracks",
        to_async(lambda query, limit: sent_queries.append(query) or []),
    )
    monkeypatch.setattr(search_cache_service, "save_search_cache", to_async(lambda q, s, r: None))

    await search_cache_service.search_tracks_cached("  Beatles  ", limit=10)

    assert sent_queries == ["  Beatles  "]
