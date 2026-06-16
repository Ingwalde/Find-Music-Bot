import asyncio
import time

import httpx

from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

_access_token: str | None = None
_token_expires_at: float = 0
_spotify_access_blocked_until: float = 0
_spotify_access_block_reason: str | None = None
_spotify_runtime_lock = asyncio.Lock()


class SpotifyForbiddenError(Exception):
    """
    Raised when Spotify Web API returns 403 Forbidden.
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


def handle_spotify_http_error(error: httpx.HTTPStatusError, source: str) -> None:
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


async def get_spotify_access_token() -> str | None:
    """
    Gets Spotify access token using Client Credentials Flow.
    Token is cached in memory until it expires.
    """
    global _access_token, _token_expires_at

    if not is_spotify_configured():
        logger.info("Spotify integration is disabled or credentials are not configured.")
        return None

    async with _spotify_runtime_lock:
        if time.time() < _spotify_access_blocked_until:
            logger.info("Spotify lookup skipped: %s", _spotify_access_block_reason)
            return None

        now = time.time()

        if _access_token and now < _token_expires_at - 30:
            return _access_token

    try:
        async with httpx.AsyncClient(timeout=10) as http_client:
            response = await http_client.post(
                SPOTIFY_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        try:
            handle_spotify_http_error(error, "token request")
        except (SpotifyCredentialsError, SpotifyForbiddenError) as spotify_error:
            logger.warning("Spotify token request skipped: %s", spotify_error)
            return None
        return None
    except httpx.RequestError as error:
        logger.warning("Spotify token request failed: %s", error)
        return None

    data = response.json()

    async with _spotify_runtime_lock:
        _access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        _token_expires_at = now + expires_in

        return _access_token
