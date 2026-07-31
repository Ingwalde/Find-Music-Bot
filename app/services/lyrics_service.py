from __future__ import annotations

import httpx

from app.config.settings import settings
from app.utils.http_retry import get_with_retry
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

GENIUS_SEARCH_URL = "https://api.genius.com/search"


async def find_lyrics_url(title: str, artist: str | None = None) -> str | None:
    """
    Finds Genius song page URL.
    Full lyrics are not sent automatically; the bot provides a link instead.
    """
    if not settings.GENIUS_TOKEN:
        logger.warning("GENIUS_TOKEN is not set. Lyrics lookup is disabled.")
        return None

    query = f"{artist} {title}" if artist else title

    try:
        logger.info("Searching Genius page for: %s - %s", title, artist)

        async with httpx.AsyncClient(timeout=10) as http_client:
            response = await get_with_retry(
                http_client,
                GENIUS_SEARCH_URL,
                service="genius",
                headers={"Authorization": f"Bearer {settings.GENIUS_TOKEN}"},
                params={"q": query},
            )
        hits = response.json().get("response", {}).get("hits", [])
    except Exception as error:
        logger.warning("Genius search error: %s", error)
        return None

    if not hits:
        return None

    return hits[0].get("result", {}).get("url")
