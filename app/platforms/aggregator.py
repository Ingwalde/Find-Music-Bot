from app.config.settings import settings
from app.database.spotify_repository import (
    get_spotify_data_by_deezer_id,
    update_spotify_data_for_track,
)
from app.platforms.spotify.auth import SpotifyCredentialsError, SpotifyForbiddenError
from app.platforms.spotify.client import search_spotify_track
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def enrich_track_with_platform_links(track: dict) -> dict:
    """
    Adds optional platform links to track dictionary.

    Deezer is the source of truth for search results. Spotify is used only as an optional
    additional link when credentials and API access are available.
    """
    if not settings.spotify_enabled:
        return track

    deezer_track_id = track.get("deezer_track_id")

    if not deezer_track_id:
        return track

    cached_spotify_data = await get_spotify_data_by_deezer_id(deezer_track_id)

    if cached_spotify_data:
        track["spotify_track_id"] = cached_spotify_data.get("spotify_track_id")
        track["spotify_link"] = cached_spotify_data.get("spotify_link")
        return track

    try:
        spotify_track = await search_spotify_track(
            title=track.get("title", ""),
            artist=track.get("artist"),
        )

        if not spotify_track:
            return track

        await update_spotify_data_for_track(
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
        logger.warning("Platform enrichment failed for %s: %s", deezer_track_id, error)
        return track


async def enrich_track_with_spotify_link(track: dict) -> dict:
    """
    Backward-compatible alias for the old service name.
    """
    return await enrich_track_with_platform_links(track)
