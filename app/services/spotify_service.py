import time
from difflib import SequenceMatcher

import requests
from requests import HTTPError

from app.config.settings import settings
from app.utils.logger import setup_logger


logger = setup_logger(__name__)

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

_access_token: str | None = None
_token_expires_at: float = 0
_spotify_access_blocked_until: float = 0
_spotify_access_block_reason: str | None = None


class SpotifyForbiddenError(Exception):
    """
    Raised when Spotify Web API returns 403 Forbidden.
    Usually means the app does not have access to the requested Web API endpoint.
    """


class SpotifyCredentialsError(Exception):
    """
    Raised when Spotify credentials are invalid or token request fails because of auth.
    """


def is_spotify_configured() -> bool:
    """
    Returns True when Spotify credentials are configured and integration is enabled.
    """
    return settings.spotify_enabled


def is_spotify_temporarily_blocked() -> bool:
    """
    Returns True if Spotify lookup is temporarily disabled after access errors.
    """
    return time.time() < _spotify_access_blocked_until


def get_spotify_block_reason() -> str | None:
    """
    Returns the last Spotify access block reason.
    """
    return _spotify_access_block_reason


def disable_spotify_temporarily(reason: str) -> None:
    """
    Temporarily disables Spotify lookups to avoid repeated 403 warnings and delays.
    """
    global _spotify_access_blocked_until, _spotify_access_block_reason

    _spotify_access_block_reason = reason
    _spotify_access_blocked_until = time.time() + settings.SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS

    logger.warning(
        "Spotify lookup temporarily disabled for %s seconds. Reason: %s",
        settings.SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS,
        reason,
    )


def reset_spotify_runtime_state() -> None:
    """
    Resets Spotify token/cache runtime state. Used by tests.
    """
    global _access_token, _token_expires_at, _spotify_access_blocked_until, _spotify_access_block_reason

    _access_token = None
    _token_expires_at = 0
    _spotify_access_blocked_until = 0
    _spotify_access_block_reason = None


def normalize_text(value: str | None) -> str:
    """
    Normalizes text for approximate comparison.
    """
    if not value:
        return ""

    allowed = []

    for char in value.lower():
        if char.isalnum() or char.isspace():
            allowed.append(char)

    return " ".join("".join(allowed).split())


def similarity(left: str | None, right: str | None) -> float:
    """
    Returns similarity score between two strings.
    """
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def build_spotify_queries(title: str, artist: str | None = None) -> list[str]:
    """
    Builds Spotify search queries from strict to broad.
    Broad fallback often works better for mixed punctuation or old releases.
    """
    clean_title = title.strip()
    clean_artist = (artist or "").strip()

    queries = []

    if clean_title and clean_artist:
        queries.append(f'track:"{clean_title}" artist:"{clean_artist}"')
        queries.append(f"{clean_title} {clean_artist}")

    if clean_title:
        queries.append(clean_title)

    # Preserve order and remove duplicates.
    return list(dict.fromkeys(query for query in queries if query))


def handle_spotify_http_error(error: HTTPError, source: str) -> None:
    """
    Handles Spotify HTTP errors and converts known access errors to clearer exceptions.
    """
    response = error.response
    status_code = response.status_code if response is not None else None

    if status_code == 401:
        raise SpotifyCredentialsError(
            "Spotify returned 401 Unauthorized. Check SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        ) from error

    if status_code == 403:
        reason = (
            f"Spotify returned 403 Forbidden during {source}. "
            "Check Web API access, app mode, account permissions, Premium requirement, or Spotify Developer settings."
        )
        disable_spotify_temporarily(reason)
        raise SpotifyForbiddenError(reason) from error

    raise error


def get_spotify_access_token() -> str | None:
    """
    Gets Spotify access token using Client Credentials Flow.
    Token is cached in memory until it expires.
    """
    global _access_token, _token_expires_at

    if not is_spotify_configured():
        logger.info("Spotify integration is disabled or credentials are not configured.")
        return None

    if is_spotify_temporarily_blocked():
        logger.info("Spotify lookup skipped: %s", get_spotify_block_reason())
        return None

    now = time.time()

    if _access_token and now < _token_expires_at - 30:
        return _access_token

    try:
        response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        response.raise_for_status()
    except HTTPError as error:
        handle_spotify_http_error(error, "token request")
        return None
    except requests.RequestException as error:
        logger.warning("Spotify token request failed: %s", error)
        return None

    data = response.json()

    _access_token = data.get("access_token")
    expires_in = int(data.get("expires_in", 3600))
    _token_expires_at = now + expires_in

    return _access_token


def format_spotify_track(item: dict) -> dict:
    """
    Normalizes Spotify track item into a simple dictionary.
    """
    artists = item.get("artists") or []
    album = item.get("album") or {}
    external_urls = item.get("external_urls") or {}

    artist_names = ", ".join(
        artist.get("name", "Unknown artist")
        for artist in artists
        if artist.get("name")
    )

    return {
        "spotify_track_id": item.get("id"),
        "spotify_title": item.get("name"),
        "spotify_artist": artist_names,
        "spotify_album": album.get("name"),
        "spotify_link": external_urls.get("spotify"),
    }


def score_spotify_candidate(
    candidate: dict,
    title: str,
    artist: str | None,
) -> float:
    """
    Scores Spotify search result against Deezer track metadata.
    """
    title_score = similarity(candidate.get("spotify_title"), title)
    artist_score = similarity(candidate.get("spotify_artist"), artist or "")

    if artist:
        return (title_score * 0.7) + (artist_score * 0.3)

    return title_score


def request_spotify_search(
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
        response = requests.get(
            SPOTIFY_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        response.raise_for_status()
    except HTTPError as error:
        handle_spotify_http_error(error, "track search")
        return []
    except requests.RequestException as error:
        logger.warning("Spotify search request failed: %s", error)
        return []

    data = response.json()
    return data.get("tracks", {}).get("items", [])


def search_spotify_track(
    title: str,
    artist: str | None = None,
    limit: int = 5,
) -> dict | None:
    """
    Searches Spotify for the closest matching track.
    Returns normalized track data or None.
    """
    token = get_spotify_access_token()

    if not token:
        return None

    all_items = []

    for query in build_spotify_queries(title, artist):
        items = request_spotify_search(
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
