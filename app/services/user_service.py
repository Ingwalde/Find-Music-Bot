"""
User state: identity, language preference, last viewed track.

This module exists to own the bot layer's access to user tables. `app/bot`
previously imported `app.database.repositories` directly, which made the
layering a convention rather than a boundary — `tests/test_architecture_imports.py`
now enforces the direction, and this is the seam it enforces against.

The functions are re-exported unchanged rather than wrapped. There is no
business logic to add on top of a single-row lookup, and a wrapper that only
forwards its arguments would claim an encapsulation that is not there. What
the module buys is the boundary itself: when one of these does grow logic —
caching a language, validating a code — it grows here, and no caller changes.
"""

from app.database.repositories import (
    get_last_track_id,
    get_user_language,
    save_last_track_id,
    set_user_language,
    upsert_user,
)

__all__ = [
    "get_last_track_id",
    "get_user_language",
    "save_last_track_id",
    "set_user_language",
    "upsert_user",
]
