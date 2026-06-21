import httpx

from app.config.settings import settings
from app.platforms.spotify.auth import (
    SpotifyCredentialsError,
    SpotifyForbiddenError,
    get_spotify_access_token,
    handle_spotify_http_error,
)
from app.platforms.spotify.matcher import (
    build_spotify_queries,
    format_spotify_track,
    score_spotify_candidate,
)
from app.utils.http_retry import get_with_retry
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"


async def request_spotify_search(
    token: str,
    query: str,
    limit: int,
    market: str | None,
) -> list[dict]:
    """
    Sends one Spotify search request and returns track items.
    """
    params = {
        "q": query,
        "type": "track",
        "limit": limit,
    }

    if market:
        params["market"] = market

    try:
        async with httpx.AsyncClient(timeout=10) as http_client:
            response = await get_with_retry(
                http_client,
                SPOTIFY_SEARCH_URL,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
    except httpx.HTTPStatusError as error:
        try:
            handle_spotify_http_error(error, "track search")
        except (SpotifyCredentialsError, SpotifyForbiddenError) as spotify_error:
            logger.warning("Spotify search skipped: %s", spotify_error)
            return []
        return []
    except httpx.RequestError as error:
        logger.warning("Spotify search request failed: %s", error)
        return []

    data = response.json()
    return data.get("tracks", {}).get("items", [])


async def search_spotify_track(
    title: str,
    artist: str | None = None,
    limit: int = 5,
) -> dict | None:
    """
    Searches Spotify for the closest matching track.
    Returns normalized track data or None.
    """
    token = await get_spotify_access_token()

    if not token:
        return None

    all_items = []

    for query in build_spotify_queries(title, artist):
        items = await request_spotify_search(
            token=token,
            query=query,
            limit=limit,
            market=settings.SPOTIFY_MARKET,
        )

        if items:
            all_items.extend(items)
            break

    if not all_items:
        return None

    candidates = [format_spotify_track(item) for item in all_items]
    candidates = [candidate for candidate in candidates if candidate.get("spotify_link")]

    if not candidates:
        return None

    candidates.sort(
        key=lambda candidate: score_spotify_candidate(candidate, title, artist),
        reverse=True,
    )

    best_candidate = candidates[0]
    score = score_spotify_candidate(best_candidate, title, artist)

    if score < 0.45:
        logger.info(
            "Spotify match score is low for %s — %s: %.2f",
            artist,
            title,
            score,
        )

    return best_candidate
