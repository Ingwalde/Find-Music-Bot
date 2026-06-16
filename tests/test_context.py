import asyncio

import pytest

from app.bot.context import (
    get_current_page,
    get_page_tracks,
    get_search_context,
    get_total_pages,
    save_search_context,
    set_search_page,
)


def make_tracks(count: int) -> list[dict]:
    return [{"deezer_track_id": str(index), "title": f"Track {index}"} for index in range(count)]


@pytest.mark.asyncio
async def test_save_and_get_search_context():
    tracks = make_tracks(3)

    await save_search_context(user_id=1, query="test", tracks=tracks)

    context = await get_search_context(1)

    assert context["query"] == "test"
    assert context["tracks"] == tracks
    assert context["page"] == 0


@pytest.mark.asyncio
async def test_get_total_pages():
    await save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    assert await get_total_pages(user_id=1, page_size=5) == 3


@pytest.mark.asyncio
async def test_get_page_tracks_returns_expected_slice():
    await save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    page_zero = await get_page_tracks(user_id=1, page_size=5, page=0)
    page_two = await get_page_tracks(user_id=1, page_size=5, page=2)

    assert [track["title"] for track in page_zero] == [
        "Track 0",
        "Track 1",
        "Track 2",
        "Track 3",
        "Track 4",
    ]
    assert [track["title"] for track in page_two] == ["Track 10", "Track 11"]


@pytest.mark.asyncio
async def test_set_search_page_normalizes_low_and_high_values():
    await save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    assert await set_search_page(user_id=1, page=-10, page_size=5) == 0
    assert await get_current_page(1) == 0

    assert await set_search_page(user_id=1, page=999, page_size=5) == 2
    assert await get_current_page(1) == 2


@pytest.mark.asyncio
async def test_missing_context_returns_safe_defaults():
    assert await get_search_context(999) is None
    assert await get_total_pages(user_id=999, page_size=5) == 0
    assert await get_page_tracks(user_id=999, page_size=5) == []
    assert await get_current_page(999) == 0


@pytest.mark.asyncio
async def test_search_context_expires(monkeypatch):
    from app.bot import context

    monkeypatch.setattr(context, "SEARCH_CONTEXT_TTL_SECONDS", 10)
    monkeypatch.setattr(context, "time", lambda: 100.0)
    await context.save_search_context(user_id=55, query="old", tracks=make_tracks(1))

    monkeypatch.setattr(context, "time", lambda: 111.0)

    assert await context.get_search_context(55) is None
    assert 55 not in context.search_contexts


@pytest.mark.asyncio
async def test_cleanup_expired_search_contexts(monkeypatch):
    from app.bot import context

    context.search_contexts.clear()
    context.search_contexts[1] = {"query": "old", "tracks": [], "page": 0, "created_at": 0.0}
    context.search_contexts[2] = {"query": "new", "tracks": [], "page": 0, "created_at": 95.0}
    monkeypatch.setattr(context, "SEARCH_CONTEXT_TTL_SECONDS", 10)

    assert await context.cleanup_expired_search_contexts(now=100.0) == 1
    assert 1 not in context.search_contexts
    assert 2 in context.search_contexts


@pytest.mark.asyncio
async def test_concurrent_save_and_get_for_different_users_does_not_corrupt_state():
    async def save_and_fetch(user_id: int, query: str, count: int) -> dict:
        await save_search_context(user_id=user_id, query=query, tracks=make_tracks(count))
        return await get_search_context(user_id)

    result_1, result_2 = await asyncio.gather(
        save_and_fetch(101, "alpha", 3),
        save_and_fetch(102, "beta", 5),
    )

    assert result_1["query"] == "alpha"
    assert len(result_1["tracks"]) == 3
    assert result_2["query"] == "beta"
    assert len(result_2["tracks"]) == 5
