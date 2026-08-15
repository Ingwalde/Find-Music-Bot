"""Covers the v3.7.x audit fixes: idle eviction, batch counts, cache prune."""

from collections import deque

import pytest

import app.bot.rate_limit as rate_limit
import app.database.maintenance as maintenance
import app.services.recommendations_service as recommendations
from tests.conftest import to_async

# ── rate limiter: idle eviction (was an unbounded leak) ──────────────────────


def test_evict_idle_drops_users_past_their_window():
    rate_limit._request_timestamps.clear()
    rate_limit._warned_users.clear()

    rate_limit._request_timestamps[1] = deque([100.0])  # idle
    rate_limit._request_timestamps[2] = deque([195.0])  # recent
    rate_limit._request_timestamps[3] = deque()  # drained
    rate_limit._warned_users.update({1, 2, 3})

    rate_limit._evict_idle_unlocked(current_time=200.0, window=60.0)

    assert set(rate_limit._request_timestamps) == {2}
    assert rate_limit._warned_users == {2}


def test_evict_idle_keeps_everything_inside_the_window():
    rate_limit._request_timestamps.clear()
    rate_limit._request_timestamps[1] = deque([190.0])
    rate_limit._request_timestamps[2] = deque([199.0])

    rate_limit._evict_idle_unlocked(current_time=200.0, window=60.0)

    assert set(rate_limit._request_timestamps) == {1, 2}


@pytest.mark.asyncio
async def test_memory_limiter_sweeps_once_over_the_threshold(monkeypatch):
    """The sweep is what stops the dict growing forever without Redis."""
    rate_limit._request_timestamps.clear()
    rate_limit._warned_users.clear()
    monkeypatch.setattr(rate_limit, "_EVICT_THRESHOLD", 5)

    # Ten users that will never be seen again.
    for user_id in range(1000, 1010):
        rate_limit._request_timestamps[user_id] = deque([0.0])

    assert await rate_limit._check_rate_limit_memory(telegram_id=42) is True

    # The stale ten are gone; only the live caller remains.
    assert set(rate_limit._request_timestamps) == {42}


@pytest.mark.asyncio
async def test_memory_limiter_does_not_sweep_below_the_threshold(monkeypatch):
    rate_limit._request_timestamps.clear()
    monkeypatch.setattr(rate_limit, "_EVICT_THRESHOLD", 1000)
    rate_limit._request_timestamps[999] = deque([0.0])

    await rate_limit._check_rate_limit_memory(telegram_id=42)

    assert 999 in rate_limit._request_timestamps


# ── maintenance: batched table counts ───────────────────────────────────────


@pytest.mark.asyncio
async def test_table_counts_uses_one_query(monkeypatch):
    queries: list[str] = []

    class FakeConn:
        async def fetch(self, query, *args):
            queries.append(query)
            return [
                {"table_name": "users", "row_count": 7},
                {"table_name": "tracks", "row_count": 3},
            ]

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, *args):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(
        maintenance, "get_maintenance_table_names", to_async(lambda: ("users", "tracks"))
    )
    monkeypatch.setattr(maintenance, "get_pool", to_async(lambda: FakePool()))

    counts = await maintenance.get_table_counts()

    assert counts == {"users": 7, "tracks": 3}
    assert len(queries) == 1
    assert "UNION ALL" in queries[0]


@pytest.mark.asyncio
async def test_table_counts_preserves_allowlist_order(monkeypatch):
    class FakeConn:
        async def fetch(self, query, *args):
            # Deliberately reversed relative to the allowlist.
            return [
                {"table_name": "tracks", "row_count": 3},
                {"table_name": "users", "row_count": 7},
            ]

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, *args):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquire()

    monkeypatch.setattr(
        maintenance, "get_maintenance_table_names", to_async(lambda: ("users", "tracks"))
    )
    monkeypatch.setattr(maintenance, "get_pool", to_async(lambda: FakePool()))

    assert list(await maintenance.get_table_counts()) == ["users", "tracks"]


@pytest.mark.asyncio
async def test_table_counts_returns_empty_without_tables(monkeypatch):
    monkeypatch.setattr(maintenance, "get_maintenance_table_names", to_async(lambda: ()))

    assert await maintenance.get_table_counts() == {}


# ── recommendations: concurrent related-artist fetch ────────────────────────


@pytest.mark.asyncio
async def test_one_failing_related_artist_does_not_lose_the_others(monkeypatch):
    """return_exceptions=True is why a single bad artist can't empty the batch."""

    async def fake_top_tracks(artist_id, limit=10):
        if artist_id == "bad":
            raise RuntimeError("deezer down")
        return [{"deezer_track_id": f"t{artist_id}", "rank": 100}]

    monkeypatch.setattr(
        recommendations, "get_artist_top_tracks", to_async(lambda artist_name, limit: [])
    )
    monkeypatch.setattr(recommendations, "get_artist_id", to_async(lambda name: "a1"))
    monkeypatch.setattr(
        recommendations,
        "get_related_artists",
        to_async(lambda artist_id, limit: [{"id": "good"}, {"id": "bad"}]),
    )
    monkeypatch.setattr(recommendations, "get_artist_top_tracks_by_id", fake_top_tracks)
    monkeypatch.setattr(recommendations, "get_track_by_deezer_id", to_async(lambda tid: None))

    result = await recommendations.get_similar_by_genre(
        track_id="999", artist_name="ABBA", limit=5
    )

    assert [t["deezer_track_id"] for t in result] == ["tgood"]
