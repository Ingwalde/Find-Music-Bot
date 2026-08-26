import asyncio
import json
import time

import httpx

from app.config.settings import settings
from app.utils.http_client import get_http_client
from app.utils.http_retry import post_with_retry
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

# The reason string is surfaced to admins via /health and carried for the whole
# cooldown, so a long body would push the rest of the readout out of view.
_MAX_ERROR_DETAIL_CHARS = 200

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


def _spotify_error_detail(response: httpx.Response | None) -> str | None:
    """
    Extracts the human-readable half of a Spotify error body, if there is one.

    Spotify does not answer errors consistently. A 403 from the token endpoint
    arrives as bare text with no Content-Type header at all -- the common one
    being "Active premium subscription required for the owner of the app." --
    while Web API errors use {"error": {"message": ...}} and the token endpoint's
    auth failures use {"error": "...", "error_description": "..."}. Sniffing the
    body instead of trusting the header is what makes all three readable.

    Returns None when there is nothing worth showing, so the caller can fall
    back to generic guidance rather than print an empty or raw-JSON reason.
    """
    if response is None:
        return None

    try:
        body = response.text.strip()
    except (UnicodeDecodeError, httpx.ResponseNotRead):
        return None

    if not body:
        return None

    # `[` as well as `{`: a body that is structured data is never shown raw,
    # whether or not we can find a message inside it.
    if body[0] in "{[":
        try:
            payload = json.loads(body)
        except ValueError:
            return None

        if not isinstance(payload, dict):
            return None

        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
        else:
            # Token endpoint: the description carries the detail, the code alone
            # ("invalid_client") is what we already knew from the status.
            message = payload.get("error_description") or error

        if not isinstance(message, str) or not message.strip():
            return None

        body = message.strip()

    # Collapses the newlines Spotify puts in plain-text bodies; the reason goes
    # into a single log line and a single Telegram message.
    body = " ".join(body.split())

    if len(body) > _MAX_ERROR_DETAIL_CHARS:
        body = body[: _MAX_ERROR_DETAIL_CHARS - 1].rstrip() + "…"

    return body or None


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
        # Spotify's own wording is far more actionable than the generic list
        # when it bothers to send one -- "Active premium subscription required
        # for the owner of the app" names the actual cause, whereas the list
        # below leaves the admin to guess which of five things went wrong.
        detail = _spotify_error_detail(response)
        reason = f"Spotify returned 403 Forbidden during {source}. " + (
            detail
            or "Check Web API access, app mode, account permissions, "
            "Premium requirement, or Spotify Developer settings."
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

    # Held for the whole fetch-or-return flow, not just the cache read/write:
    # a second concurrent caller waits here and then sees the freshly cached
    # token below instead of independently re-fetching (avoids duplicate
    # outbound requests to Spotify under concurrent load).
    async with _spotify_runtime_lock:
        if time.time() < _spotify_access_blocked_until:
            logger.info("Spotify lookup skipped: %s", _spotify_access_block_reason)
            return None

        now = time.time()

        if _access_token and now < _token_expires_at - 30:
            return _access_token

        try:
            response = await post_with_retry(
                get_http_client(),
                SPOTIFY_TOKEN_URL,
                service="spotify",
                data={"grant_type": "client_credentials"},
                auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            )
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

        _access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        _token_expires_at = now + expires_in

        return _access_token
