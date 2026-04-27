import deezer

from app.utils.time import convert_duration
from app.utils.logger import setup_logger


logger = setup_logger(__name__)

client = deezer.Client()


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

    return {
        "deezer_track_id": str(track.id),
        "title": str(track.title),
        "artist": artist_name,
        "album": album_name,
        "duration": convert_duration(track.duration),
        "duration_seconds": int(track.duration),
        "deezer_link": str(track.link),
        "cover_url": cover_url,
    }


def search_tracks(query: str, limit: int = 10) -> list[dict]:
    """
    Searches tracks in Deezer.
    """
    query = query.strip()

    if not query:
        return []

    logger.info("Searching Deezer tracks for query: %s", query)

    results = client.search(query)

    if not results:
        return []

    tracks = []

    for track in results[:limit]:
        tracks.append(format_deezer_track(track))

    return tracks


def get_track(track_id: str | int) -> dict:
    """
    Gets single track by Deezer track ID.
    """
    logger.info("Getting Deezer track by ID: %s", track_id)

    track = client.get_track(int(track_id))

    return format_deezer_track(track)
