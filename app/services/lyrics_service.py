import lyricsgenius

from app.config.settings import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def create_genius_client():
    """
    Creates Genius client only if token exists.
    Compatible with different lyricsgenius versions.
    """
    if not settings.GENIUS_TOKEN:
        logger.warning("GENIUS_TOKEN is not set. Lyrics lookup is disabled.")
        return None

    try:
        genius_client = lyricsgenius.Genius(
            settings.GENIUS_TOKEN,
            timeout=10,
        )

        if hasattr(genius_client, "verbose"):
            genius_client.verbose = False

        if hasattr(genius_client, "remove_section_headers"):
            genius_client.remove_section_headers = True

        if hasattr(genius_client, "skip_non_songs"):
            genius_client.skip_non_songs = True

        return genius_client

    except Exception as error:
        logger.warning("Could not create Genius client: %s", error)
        return None


genius = create_genius_client()


def find_lyrics_url(title: str, artist: str | None = None) -> str | None:
    """
    Finds Genius song page URL.
    Full lyrics are not sent automatically; the bot provides a link instead.
    """
    if genius is None:
        return None

    try:
        logger.info("Searching Genius page for: %s - %s", title, artist)

        song = genius.search_song(
            title=title,
            artist=artist,
        )

        if not song:
            return None

        return getattr(song, "url", None)

    except Exception as error:
        logger.warning("Genius search error: %s", error)
        return None
