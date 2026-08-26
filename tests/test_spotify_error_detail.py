"""
Covers `_spotify_error_detail`: surfacing Spotify's own 403 wording.

The bug this replaces: every 403 produced the same five-item checklist, so an
admin reading /health could not tell "the app is in development mode" from "the
owner's Premium lapsed" -- Spotify says which, and we were discarding it.
"""

import httpx
import pytest

from app.platforms.spotify import auth

# Verbatim body Spotify returns from the token endpoint when the app owner has
# no active subscription. Plain text, and it arrives with no Content-Type at
# all, which is why the parser sniffs the body instead of the header.
PREMIUM_BODY = (
    "Active premium subscription required for the owner of the app. "
    "When the subscription status changes, it can take a few hours before "
    "requests are allowed again."
)

GENERIC_FALLBACK = "Check Web API access, app mode, account permissions"


@pytest.fixture(autouse=True)
def reset_spotify_runtime_state():
    auth.reset_spotify_runtime_state()
    yield
    auth.reset_spotify_runtime_state()


def make_response(status_code: int, content: bytes = b"", headers: dict | None = None):
    request = httpx.Request("POST", auth.SPOTIFY_TOKEN_URL)
    return httpx.Response(status_code, request=request, content=content, headers=headers)


def forbidden_error(content: bytes = b"", headers: dict | None = None):
    response = make_response(403, content=content, headers=headers)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        response.raise_for_status()
    return exc_info.value


# -- the shapes Spotify actually sends ---------------------------------------


def test_plain_text_body_without_content_type_is_used():
    """The real-world case. No Content-Type header is set on purpose."""
    error = forbidden_error(PREMIUM_BODY.encode())

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "token request")

    reason = str(raised.value)
    assert "Active premium subscription required" in reason
    assert GENERIC_FALLBACK not in reason, "Spotify's own wording must replace the checklist"


def test_web_api_json_error_message_is_used():
    error = forbidden_error(b'{"error": {"status": 403, "message": "Player command failed"}}')

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "track lookup")

    assert "Player command failed" in str(raised.value)


def test_token_endpoint_json_uses_the_description_not_the_code():
    """`{"error": "invalid_client"}` restates the status; the description does not."""
    body = b'{"error": "invalid_client", "error_description": "Invalid client secret"}'
    error = forbidden_error(body)

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "token request")

    assert "Invalid client secret" in str(raised.value)


# -- falling back rather than printing something useless ---------------------


@pytest.mark.parametrize(
    ("body", "why"),
    [
        (b"", "empty body"),
        (b"   \n  ", "whitespace only"),
        (b"{not json at all", "looks like JSON, is not"),
        (b'{"error": {"status": 403}}', "JSON with no message field"),
        (b'{"error": {"message": ""}}', "JSON with an empty message"),
        (b'["unexpected"]', "valid JSON, wrong shape"),
    ],
)
def test_unusable_bodies_fall_back_to_the_generic_guidance(body, why):
    error = forbidden_error(body)

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "token request")

    reason = str(raised.value)
    assert GENERIC_FALLBACK in reason, why
    # The raw body must never leak through as the explanation.
    assert "{" not in reason


def test_detail_of_none_response_is_none():
    assert auth._spotify_error_detail(None) is None


# -- shaping the string for a log line and a Telegram message ----------------


def test_long_body_is_truncated():
    error = forbidden_error(b"x" * 900)

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "token request")

    detail = str(raised.value).split("token request. ", 1)[1]
    assert len(detail) == auth._MAX_ERROR_DETAIL_CHARS
    assert detail.endswith("…")


def test_multiline_body_is_collapsed_to_one_line():
    error = forbidden_error(b"first line\n\nsecond   line\ttab")

    detail = auth._spotify_error_detail(error.response)

    assert detail == "first line second line tab"


# -- the reason has to reach the place an admin reads it ---------------------


def test_detail_reaches_the_cooldown_reason_shown_by_health():
    """
    /health reports `_spotify_access_block_reason` for the whole cooldown, so a
    detail that only reached the raised exception would still leave the admin
    reading the generic checklist an hour later.
    """
    error = forbidden_error(PREMIUM_BODY.encode())

    with pytest.raises(auth.SpotifyForbiddenError):
        auth.handle_spotify_http_error(error, "token request")

    assert "Active premium subscription required" in auth._spotify_access_block_reason


def test_source_is_still_named_in_the_reason():
    """Which call tripped the cooldown stays useful; the detail adds to it."""
    error = forbidden_error(PREMIUM_BODY.encode())

    with pytest.raises(auth.SpotifyForbiddenError) as raised:
        auth.handle_spotify_http_error(error, "track lookup")

    assert "403 Forbidden during track lookup" in str(raised.value)


def test_401_is_untouched_by_this_change():
    response = make_response(401, content=b"some 401 body")
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        response.raise_for_status()

    with pytest.raises(auth.SpotifyCredentialsError) as raised:
        auth.handle_spotify_http_error(exc_info.value, "token request")

    assert "SPOTIFY_CLIENT_ID" in str(raised.value)
