import asyncio
import json
from collections.abc import Awaitable, Callable
from time import time

from redis.exceptions import RedisError

from app.database.repositories import get_track_by_deezer_id, get_tracks_by_artist
from app.services.deezer_service import (
    get_artist_id,
    get_artist_top_tracks,
    get_artist_top_tracks_by_id,
    get_related_artists,
)
from app.utils.logger import setup_logger
from app.utils.types import TrackDict

logger = setup_logger(__name__)

_TRENDING_TTL = 3600
_TRENDING_REDIS_KEY = "trending:tracks"

_trending_cache: dict = {"tracks": [], "expires_at": 0.0}
_trending_cache_lock = asyncio.Lock()


async def get_cached_trending(fetch_fn: Callable[[int], Awaitable[list[TrackDict]]], limit: int = 10) -> list[TrackDict]:
    """
    Returns trending tracks, checking Redis first (if available), then in-memory,
    then fetching fresh. TTL is 1 hour in both backends.
    """
    from app.services.redis_client import get_redis_client

    client = get_redis_client()
    if client is not None:
        try:
            cached = await client.get(_TRENDING_REDIS_KEY)
            if cached:
                logger.info("Returning trending tracks from Redis cache")
                return json.loads(cached)
        except (RedisError, OSError):
            logger.warning("Redis trending cache read failed, using in-memory fallback")

    async with _trending_cache_lock:
        if time() < _trending_cache["expires_at"] and _trending_cache["tracks"]:
            logger.info("Returning trending tracks from in-memory cache")
            return list(_trending_cache["tracks"])

    logger.info("Cache expired or empty — fetching trending tracks")
    tracks = await fetch_fn(limit)

    if client is not None:
        try:
            await client.set(_TRENDING_REDIS_KEY, json.dumps(tracks), ex=_TRENDING_TTL)
            logger.info("Trending tracks stored in Redis cache")
            return tracks
        except (RedisError, OSError):
            logger.warning("Redis trending cache write failed, using in-memory fallback")

    async with _trending_cache_lock:
        _trending_cache["tracks"] = tracks
        _trending_cache["expires_at"] = time() + _TRENDING_TTL

    return tracks


def invalidate_trending_cache() -> None:
    """Resets the in-memory trending cache. For tests and emergency cache busting."""
    _trending_cache["tracks"] = []
    _trending_cache["expires_at"] = 0.0


async def get_db_recommendations(artist: str, exclude_deezer_id: str, limit: int = 3) -> list[TrackDict]:
    """
    Returns recommended tracks by artist from local DB.
    Falls back to Deezer artist top tracks if DB has no results.
    """
    tracks = await get_tracks_by_artist(
        artist=artist,
        exclude_deezer_id=exclude_deezer_id,
        limit=limit,
    )

    if tracks:
        logger.info("DB recommendations for %r: %d track(s)", artist, len(tracks))
        return tracks  # type: ignore[return-value]

    logger.info("No DB recommendations for %r — falling back to Deezer artist API", artist)
    return await get_artist_top_tracks(artist_name=artist, limit=limit)


def _get_decade(release_date: str | None) -> tuple[int, int] | None:
    """Returns (decade_start, decade_end) from a date string, or None if unparseable."""
    if not release_date:
        return None
    try:
        year = int(release_date[:4])
    except (ValueError, TypeError):
        return None
    if year < 1900 or year > 2100:
        return None
    decade_start = (year // 10) * 10
    return decade_start, decade_start + 9


async def get_similar_by_genre(track_id: str, artist_name: str = "", limit: int = 10) -> list[TrackDict]:
    """
    Returns tracks similar to the given track using a 3-step strategy.
    Step 1: top tracks by the same artist (up to 5, excluding current track).
    Step 2: fill remaining slots with top tracks by related artists, filtered by rank
            proximity and deduped against Step 1 results.
    Step 3: fallback to artist top tracks without rank filter if steps 1+2 gave nothing.
    """
    # Step 1 — artist tracks
    artist_raw = await get_artist_top_tracks(artist_name=artist_name, limit=5)
    result = [t for t in artist_raw if t.get("deezer_track_id") != str(track_id)]

    # Step 2 — related artists fill if we have room
    if len(result) < limit:
        artist_id = await get_artist_id(artist_name)
        related = await get_related_artists(artist_id, limit=3) if artist_id else []

        if related:
            db_track = await get_track_by_deezer_id(track_id)
            rank = db_track.get("rank") if db_track else None
            decade = _get_decade(db_track.get("release_date") if db_track else None)

            seen_ids = {str(track_id)} | {t["deezer_track_id"] for t in result if t.get("deezer_track_id")}
            needed = limit - len(result)

            candidates: list[TrackDict] = []
            for artist in related:
                candidates.extend(await get_artist_top_tracks_by_id(artist["id"], limit=10))

            # Pass A — with decade filter
            decade_results: list[TrackDict] = []
            for t in candidates:
                tid = t.get("deezer_track_id", "")
                if tid in seen_ids:
                    continue
                t_rank = t.get("rank")
                if rank and t_rank is not None and not (rank * 0.1 <= t_rank <= rank * 3.0):
                    continue
                if decade is not None:
                    t_date = t.get("release_date")
                    if t_date:
                        t_decade = _get_decade(t_date)
                        if t_decade is not None and t_decade[0] != decade[0]:
                            continue
                decade_results.append(t)
                seen_ids.add(tid)

            # Pass B — rank filter only, when Pass A gave too few results
            fill_results: list[TrackDict] = []
            if len(decade_results) < 5:
                for t in candidates:
                    tid = t.get("deezer_track_id", "")
                    if tid in seen_ids:
                        continue
                    t_rank = t.get("rank")
                    if rank and t_rank is not None and not (rank * 0.1 <= t_rank <= rank * 3.0):
                        continue
                    fill_results.append(t)
                    seen_ids.add(tid)

            result.extend((decade_results + fill_results)[:needed])

    # Step 3 — fallback if both steps gave nothing
    if not result:
        logger.info("Similar steps 1+2 empty for %s — using artist fallback", track_id)
        return await get_artist_top_tracks(artist_name=artist_name, limit=limit)

    logger.info("Similar tracks for %s: %d result(s)", track_id, len(result))
    return result[:limit]


def _format_grouped(tracks: list[TrackDict], source_artist: str) -> str:
    same, others = [], []
    for track in tracks:
        if track.get("artist", "") == source_artist:
            same.append(track)
        else:
            others.append(track)

    sections = []

    if same:
        lines = [f"🎤 {source_artist}"]
        for track in same:
            title = track.get("title", "Unknown")
            link = track.get("deezer_link", "")
            if link:
                lines.append(f"- [{title}]({link})")
            else:
                lines.append(f"- {title}")
        sections.append("\n".join(lines))

    if others:
        lines = ["🎵 Others"]
        for track in others:
            title = track.get("title", "Unknown")
            artist = track.get("artist", "Unknown artist")
            link = track.get("deezer_link", "")
            if link:
                lines.append(f"- [{title}]({link}) — {artist}")
            else:
                lines.append(f"- {title} — {artist}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _format_numbered(tracks: list[TrackDict]) -> str:
    lines = []
    for i, track in enumerate(tracks, start=1):
        title = track.get("title", "Unknown")
        artist = track.get("artist", "Unknown artist")
        link = track.get("deezer_link", "")
        if link:
            lines.append(f"{i}. [{artist} — {title}]({link})")
        else:
            lines.append(f"{i}. {artist} — {title}")
    return "\n".join(lines)


def format_recommendations_text(tracks: list[TrackDict], source_artist: str = "") -> str:
    """
    Formats recommendation tracks as a text list.
    Without source_artist: numbered list (backward-compatible).
    With source_artist: grouped by 🎤 same artist / 🎵 Others.
    Returns empty string if no tracks provided.
    """
    if not tracks:
        return ""

    if not source_artist:
        return _format_numbered(tracks)

    return _format_grouped(tracks, source_artist)


def format_similar_text(header: str, tracks: list[TrackDict], source_artist: str = "") -> str:
    """
    Formats Similar tracks with a header and grouped body.
    Groups by 🎤 source_artist / 🎵 Others when source_artist is provided.
    Falls back to numbered list when source_artist is empty.
    Returns header alone when tracks is empty.
    """
    if not tracks:
        return header

    body = _format_grouped(tracks, source_artist) if source_artist else _format_numbered(tracks)

    return f"{header}\n\n{body}"
