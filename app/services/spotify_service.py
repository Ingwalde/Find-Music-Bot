"""
Compatibility facade for Spotify integration.

The implementation is split under `app.platforms.spotify`:
- auth.py: token/cooldown/errors
- matcher.py: text normalization and scoring
- client.py: Web API search
"""

from app.platforms.spotify.auth import (
    SPOTIFY_TOKEN_URL,
    SpotifyCredentialsError,
    SpotifyForbiddenError,
    disable_spotify_temporarily,
    get_spotify_access_token,
    get_spotify_block_reason,
    handle_spotify_http_error,
    is_spotify_configured,
    is_spotify_temporarily_blocked,
    reset_spotify_runtime_state,
)
from app.platforms.spotify.client import (
    SPOTIFY_SEARCH_URL,
    request_spotify_search,
    search_spotify_track,
)
from app.platforms.spotify.matcher import (
    build_spotify_queries,
    format_spotify_track,
    normalize_text,
    score_spotify_candidate,
    similarity,
)

__all__ = [
    "SPOTIFY_TOKEN_URL",
    "SPOTIFY_SEARCH_URL",
    "SpotifyForbiddenError",
    "SpotifyCredentialsError",
    "is_spotify_configured",
    "is_spotify_temporarily_blocked",
    "get_spotify_block_reason",
    "disable_spotify_temporarily",
    "reset_spotify_runtime_state",
    "normalize_text",
    "similarity",
    "build_spotify_queries",
    "handle_spotify_http_error",
    "get_spotify_access_token",
    "format_spotify_track",
    "score_spotify_candidate",
    "request_spotify_search",
    "search_spotify_track",
]
