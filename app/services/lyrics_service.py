from __future__ import annotations

from threading import RLock
from typing import Any

import lyricsgenius

from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_genius_client: Any | None = None
_genius_client_initialized = False
_genius_client_lock = RLock()


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


def reset_genius_client() -> None:
    """
    Clears cached Genius client.
    Useful for tests and controlled runtime reloads.
    """
    global _genius_client, _genius_client_initialized

    with _genius_client_lock:
        _genius_client = None
        _genius_client_initialized = False


def get_genius_client():
    """
    Lazily creates Genius client only when lyrics lookup is requested.

    This avoids startup/import warnings and keeps the bot usable when lyrics are
    not configured.
    """
    global _genius_client, _genius_client_initialized

    with _genius_client_lock:
        if not _genius_client_initialized:
            _genius_client = create_genius_client()
            _genius_client_initialized = True

        return _genius_client


def find_lyrics_url(title: str, artist: str | None = None) -> str | None:
    """
    Finds Genius song page URL.
    Full lyrics are not sent automatically; the bot provides a link instead.
    """
    genius_client = get_genius_client()

    if genius_client is None:
        return None

    try:
        logger.info("Searching Genius page for: %s - %s", title, artist)

        song = genius_client.search_song(
            title=title,
            artist=artist,
        )

        if not song:
            return None

        return getattr(song, "url", None)

    except Exception as error:
        logger.warning("Genius search error: %s", error)
        return None
