from app.config.settings import settings
from app.database.spotify_repository import (
    get_spotify_data_by_deezer_id,
    update_spotify_data_for_track,
)
from app.services.spotify_service import (
    SpotifyCredentialsError,
    SpotifyForbiddenError,
    search_spotify_track,
)
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def enrich_track_with_spotify_link(track: dict) -> dict:
    """
    Adds spotify_link to track dictionary when Spotify integration is configured.

    Flow:
    1. Check SQLite cache.
    2. If not cached, search Spotify by title + artist.
    3. Save Spotify match to SQLite.
    4. Return updated track dictionary.
    """
    if not settings.spotify_enabled:
        return track

    deezer_track_id = track.get("deezer_track_id")

    if not deezer_track_id:
        return track

    cached_spotify_data = get_spotify_data_by_deezer_id(deezer_track_id)

    if cached_spotify_data:
        track["spotify_track_id"] = cached_spotify_data.get("spotify_track_id")
        track["spotify_link"] = cached_spotify_data.get("spotify_link")
        return track

    try:
        spotify_track = search_spotify_track(
            title=track.get("title", ""),
            artist=track.get("artist"),
        )

        if not spotify_track:
            return track

        update_spotify_data_for_track(
            deezer_track_id=deezer_track_id,
            spotify_track_id=spotify_track["spotify_track_id"],
            spotify_link=spotify_track["spotify_link"],
        )

        track["spotify_track_id"] = spotify_track["spotify_track_id"]
        track["spotify_link"] = spotify_track["spotify_link"]

        return track

    except SpotifyForbiddenError as error:
        logger.warning("Spotify access is currently unavailable: %s", error)
        return track
    except SpotifyCredentialsError as error:
        logger.warning("Spotify credentials error: %s", error)
        return track
    except Exception as error:
        logger.warning("Spotify lookup failed for %s: %s", deezer_track_id, error)
        return track
