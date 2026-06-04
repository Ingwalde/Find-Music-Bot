from __future__ import annotations

from threading import RLock
from typing import Any

import deezer

from app.utils.logger import setup_logger
from app.utils.time import convert_duration

logger = setup_logger(__name__)

_deezer_client: Any | None = None
_deezer_client_lock = RLock()


def reset_deezer_client() -> None:
    """
    Clears cached Deezer client.
    Useful for tests and controlled runtime reloads.
    """
    global _deezer_client

    with _deezer_client_lock:
        _deezer_client = None


def get_deezer_client():
    """
    Lazily creates Deezer client only when Deezer API is actually used.

    This avoids network/client side effects during module import and makes tests
    and health checks safer.
    """
    global _deezer_client

    with _deezer_client_lock:
        if _deezer_client is None:
            _deezer_client = deezer.Client()

        return _deezer_client


def get_object_value(obj, attributes: list[str], default: str = "Unknown") -> str:
    """
    Safely extracts readable value from Deezer objects.
    Prevents output like <Artist: Name> or <Album: Name>.
    """
    if obj is None:
        return default

    if isinstance(obj, str):
        return obj

    for attr in attributes:
        value = getattr(obj, attr, None)
        if value:
            return str(value)

    return default


def get_release_date(track) -> str | None:
    """
    Safely extracts track release date from Deezer track object.
    Deezer may return it as a date-like object or as a string.
    """
    release_date = getattr(track, "release_date", None)

    if not release_date:
        return None

    if hasattr(release_date, "isoformat"):
        return release_date.isoformat()

    return str(release_date)


def get_rank(track) -> int | None:
    """
    Safely extracts Deezer track rank.
    Higher rank usually means higher popularity.
    """
    rank = getattr(track, "rank", None)

    if rank is None:
        return None

    try:
        rank = int(rank)
    except (TypeError, ValueError):
        return None

    if rank <= 0:
        return None

    return rank


def get_popularity_label(rank: int | None) -> str | None:
    """
    Converts Deezer numeric rank into a user-friendly popularity label.

    These labels are our UI interpretation, not official Deezer categories.
    """
    if rank is None:
        return None

    if rank >= 700_000:
        return "Very high"

    if rank >= 400_000:
        return "High"

    if rank >= 150_000:
        return "Medium"

    return "Low"


def format_deezer_track(track) -> dict:
    """
    Converts Deezer track object to normal dictionary.
    """
    artist_name = get_object_value(
        track.artist,
        ["name", "title"],
        default="Unknown artist",
    )

    album_name = get_object_value(
        track.album,
        ["title", "name"],
        default="Unknown album",
    )

    cover_url = None

    if track.album:
        cover_url = (
            getattr(track.album, "cover_xl", None)
            or getattr(track.album, "cover_big", None)
            or getattr(track.album, "cover_medium", None)
            or getattr(track.album, "cover", None)
        )

    rank = get_rank(track)
    popularity = get_popularity_label(rank)

    return {
        "deezer_track_id": str(track.id),
        "title": str(track.title),
        "artist": artist_name,
        "album": album_name,
        "duration": convert_duration(track.duration),
        "duration_seconds": int(track.duration),
        "deezer_link": str(track.link),
        "cover_url": cover_url,
        "release_date": get_release_date(track),
        "rank": rank,
        "popularity": popularity,
    }


def search_tracks(query: str, limit: int = 10) -> list[dict]:
    """
    Searches tracks in Deezer.

    Deezer is the primary data source. If the external service fails, the bot
    returns an empty result list instead of crashing in the Telegram handler.
    """
    query = query.strip()

    if not query:
        return []

    logger.info("Searching Deezer tracks for query: %s", query)

    try:
        results = get_deezer_client().search(query)
    except Exception as error:
        logger.warning("Deezer search failed for %r: %s", query, error)
        return []

    if not results:
        return []

    tracks = []

    for track in results[:limit]:
        try:
            tracks.append(format_deezer_track(track))
        except Exception as error:
            logger.warning("Could not format Deezer track from %r: %s", query, error)

    return tracks


def get_track(track_id: str | int) -> dict:
    """
    Gets single track by Deezer track ID.

    The caller can catch exceptions and show a localized friendly message.
    """
    logger.info("Getting Deezer track by ID: %s", track_id)

    try:
        track = get_deezer_client().get_track(int(track_id))
        return format_deezer_track(track)
    except Exception as error:
        logger.warning("Deezer get_track failed for %s: %s", track_id, error)
        raise RuntimeError(f"Could not load Deezer track {track_id}") from error
