from __future__ import annotations

from app.utils.http_client import get_http_client
from app.utils.http_retry import get_with_retry
from app.utils.logger import setup_logger
from app.utils.time import convert_duration
from app.utils.types import TrackDict

DEEZER_API_BASE = "https://api.deezer.com"

logger = setup_logger(__name__)


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


def _parse_raw_track(item: dict, fallback_artist: str = "") -> TrackDict:
    """
    Parses a raw Deezer API track dict (from search/track/chart/radio endpoints)
    into a normalized format.
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


async def search_tracks(query: str, limit: int = 10) -> list[TrackDict]:
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
        response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/search",
            service="deezer",
            params={"q": query, "limit": limit},
        )
        raw_tracks = response.json().get("data", [])
    except Exception as error:
        logger.warning("Deezer search failed for %r: %s", query, error)
        return []

    tracks = []

    for item in raw_tracks[:limit]:
        try:
            tracks.append(_parse_raw_track(item))
        except Exception as error:
            logger.warning("Could not parse Deezer track from %r: %s", query, error)

    return tracks


async def get_track(track_id: str | int) -> TrackDict:
    """
    Gets single track by Deezer track ID.

    The caller can catch exceptions and show a localized friendly message.
    """
    logger.info("Getting Deezer track by ID: %s", track_id)

    try:
        response = await get_with_retry(
            get_http_client(), f"{DEEZER_API_BASE}/track/{track_id}", service="deezer"
        )
        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"].get("message", "Deezer API error"))

        return _parse_raw_track(data)
    except Exception as error:
        logger.warning("Deezer get_track failed for %s: %s", track_id, error)
        raise RuntimeError(f"Could not load Deezer track {track_id}") from error


async def get_trending_tracks(limit: int = 10) -> list[TrackDict]:
    """
    Returns top trending tracks from Deezer chart.
    Falls back to empty list on any API error.
    """
    logger.info("Getting trending tracks from Deezer chart")

    try:
        response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/chart/0/tracks",
            service="deezer",
            params={"limit": limit},
        )
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


async def get_artist_top_tracks(artist_name: str, limit: int = 3) -> list[TrackDict]:
    """
    Returns top tracks by artist name via Deezer search + artist top endpoint.
    Used as fallback when local DB has no recommendations for the artist.
    """
    logger.info("Getting top tracks for artist: %r", artist_name)

    try:
        search_response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/search",
            service="deezer",
            params={"q": artist_name, "type": "artist", "limit": 1},
        )
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
        top_response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/artist/{artist_id}/top",
            service="deezer",
            params={"limit": limit},
        )
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


async def get_artist_top_tracks_by_id(artist_id: int, limit: int = 10) -> list[TrackDict]:
    """Returns top tracks for an artist by Deezer artist ID."""
    try:
        response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/artist/{artist_id}/top",
            service="deezer",
            params={"limit": limit},
        )
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


async def get_artist_id(artist_name: str) -> int | None:
    """Returns Deezer artist ID for the given artist name, or None if not found."""
    if not artist_name:
        return None
    try:
        response = await get_with_retry(
            get_http_client(),
            f"{DEEZER_API_BASE}/search",
            service="deezer",
            params={"q": artist_name, "type": "artist"},
        )
        data = response.json().get("data", [])
        if not data:
            return None
        return data[0].get("artist", {}).get("id")
    except Exception as error:
        logger.warning("Could not find artist ID for %r: %s", artist_name, error)
        return None


async def get_related_artists(artist_id: int, limit: int = 3) -> list[dict]:
    """Returns related artists for the given Deezer artist ID."""
    try:
        response = await get_with_retry(
            get_http_client(), f"{DEEZER_API_BASE}/artist/{artist_id}/related", service="deezer"
        )
        artists = response.json().get("data", [])
        return [{"id": a.get("id"), "name": a.get("name")} for a in artists[:limit]]
    except Exception as error:
        logger.warning("Could not get related artists for artist_id=%s: %s", artist_id, error)
        return []
