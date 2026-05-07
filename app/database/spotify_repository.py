"""
Compatibility facade for Spotify repository functions.

The real implementation lives in `app.database.repository_modules.spotify`.
"""

from app.database.repository_modules.spotify import (
    get_spotify_data_by_deezer_id,
    update_spotify_data_for_track,
)

__all__ = [
    "get_spotify_data_by_deezer_id",
    "update_spotify_data_for_track",
]
