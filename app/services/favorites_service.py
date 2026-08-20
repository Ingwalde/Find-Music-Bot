"""
Favourites: adding, removing, listing and clearing a user's saved tracks.

Owns the bot layer's access to the favourites tables. See user_service for why
these are re-exports rather than wrappers.

Note that `add_favorite` already composes two writes — it upserts the track and
then links it — so the composition the bot needs lives below this layer, not in
it. `favorites_callbacks` calling `save_track()` before `add_favorite()` was a
duplicate UPSERT, removed in v3.7.10.
"""

from app.database.repositories import (
    add_favorite,
    clear_favorites,
    get_favorite_tracks,
    is_track_favorite,
    remove_favorite,
)

__all__ = [
    "add_favorite",
    "clear_favorites",
    "get_favorite_tracks",
    "is_track_favorite",
    "remove_favorite",
]
