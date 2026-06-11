from __future__ import annotations

from threading import RLock
from typing import Any

import deezer
import requests

from app.utils.logger import setup_logger
from app.utils.time import convert_duration

DEEZER_API_BASE = "https://api.deezer.com"

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


def _parse_raw_track(item: dict, fallback_artist: str = "") -> dict:
    """
    Parses a raw Deezer API track dict (from chart/radio endpoints) into
    the same normalized format as format_deezer_track.
    """
    artist_obj = item.get("artist")
    album_obj = item.get("album")

    if isinstance(artist_obj, dict):
        artist_name = artist_obj.get("name") or fallback_artist or "Unknown artist"
    else:
        artist_name = str(artist_obj) if artist_obj else (fallback_artist or "Unknown artist")

    if isinstance(album_obj, dict):
        album_name = album_obj.get("title") or "Unknown album"
        cover_url = (
            album_obj.get("cover_xl")
            or album_obj.get("cover_big")
            or album_obj.get("cover_medium")
            or album_obj.get("cover")
        )
    else:
        album_name = "Unknown album"
        cover_url = None

    raw_rank = item.get("rank")
    try:
        rank = int(raw_rank) if raw_rank else None
    except (TypeError, ValueError):
        rank = None

    raw_duration = item.get("duration") or 0

    return {
        "deezer_track_id": str(item.get("id") or ""),
        "title": str(item.get("title") or "Unknown"),
        "artist": artist_name,
        "album": album_name,
        "duration": convert_duration(raw_duration),
        "duration_seconds": int(raw_duration),
        "deezer_link": str(item.get("link") or ""),
        "cover_url": cover_url,
        "release_date": item.get("release_date"),
        "rank": rank,
        "popularity": get_popularity_label(rank),
    }


def get_trending_tracks(limit: int = 10) -> list[dict]:
    """
    Returns top trending tracks from Deezer chart.
    Falls back to empty list on any API error.
    """
    logger.info("Getting trending tracks from Deezer chart")

    try:
        response = requests.get(
            f"{DEEZER_API_BASE}/chart/0/tracks",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        raw_tracks = response.json().get("data", [])
    except Exception as error:
        logger.warning("Deezer chart endpoint failed: %s", error)
        return []

    tracks = []
    for item in raw_tracks[:limit]:
        try:
            tracks.append(_parse_raw_track(item))
        except Exception as error:
            logger.warning("Could not parse trending track item: %s", error)

    return tracks


def get_artist_top_tracks(artist_name: str, limit: int = 3) -> list[dict]:
    """
    Returns top tracks by artist name via Deezer search + artist top endpoint.
    Used as fallback when local DB has no recommendations for the artist.
    """
    logger.info("Getting top tracks for artist: %r", artist_name)

    try:
        search_response = requests.get(
            f"{DEEZER_API_BASE}/search",
            params={"q": artist_name, "type": "artist", "limit": 1},
            timeout=10,
        )
        search_response.raise_for_status()
        artists = search_response.json().get("data", [])

        if not artists:
            return []

        artist_id = artists[0].get("artist", {}).get("id")

        if not artist_id:
            return []

    except Exception as error:
        logger.warning("Deezer artist search failed for %r: %s", artist_name, error)
        return []

    try:
        top_response = requests.get(
            f"{DEEZER_API_BASE}/artist/{artist_id}/top",
            params={"limit": limit},
            timeout=10,
        )
        top_response.raise_for_status()
        raw_tracks = top_response.json().get("data", [])
    except Exception as error:
        logger.warning("Deezer artist top failed for artist_id=%s: %s", artist_id, error)
        return []

    tracks = []
    for item in raw_tracks[:limit]:
        try:
            tracks.append(_parse_raw_track(item, fallback_artist=artist_name))
        except Exception as error:
            logger.warning("Could not parse artist top track item: %s", error)

    return tracks


def get_artist_top_tracks_by_id(artist_id: int, limit: int = 10) -> list[dict]:
    """Returns top tracks for an artist by Deezer artist ID."""
    try:
        response = requests.get(
            f"{DEEZER_API_BASE}/artist/{artist_id}/top",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        raw_tracks = response.json().get("data", [])
    except Exception as error:
        logger.warning("Deezer artist top (id=%s) failed: %s", artist_id, error)
        return []

    tracks = []
    for item in raw_tracks[:limit]:
        try:
            tracks.append(_parse_raw_track(item))
        except Exception as error:
            logger.warning("Could not parse artist top track by id: %s", error)

    return tracks


def get_artist_id(artist_name: str) -> int | None:
    """Returns Deezer artist ID for the given artist name, or None if not found."""
    if not artist_name:
        return None
    try:
        response = requests.get(
            f"{DEEZER_API_BASE}/search",
            params={"q": artist_name, "type": "artist"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return None
        return data[0].get("artist", {}).get("id")
    except Exception as error:
        logger.warning("Could not find artist ID for %r: %s", artist_name, error)
        return None


def get_related_artists(artist_id: int, limit: int = 3) -> list[dict]:
    """Returns related artists for the given Deezer artist ID."""
    try:
        response = requests.get(
            f"{DEEZER_API_BASE}/artist/{artist_id}/related",
            timeout=10,
        )
        response.raise_for_status()
        artists = response.json().get("data", [])
        return [{"id": a.get("id"), "name": a.get("name")} for a in artists[:limit]]
    except Exception as error:
        logger.warning("Could not get related artists for artist_id=%s: %s", artist_id, error)
        return []
