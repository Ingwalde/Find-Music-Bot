"""
Compatibility facade for repository functions.

The repository code is split into focused modules under `app.database.repository_modules`.
This file keeps old imports working, for example:
    from app.database.repositories import save_track, get_user_language
"""

from app.database.maintenance import (
    cleanup_old_errors,
    cleanup_search_history,
    get_database_summary,
)
from app.database.repository_modules.errors import clear_errors, get_recent_errors, save_error
from app.database.repository_modules.favorites import (
    add_favorite,
    clear_favorites,
    get_favorite_tracks,
    is_track_favorite,
    remove_favorite,
)
from app.database.repository_modules.search_cache import get_cached_search, save_search_cache
from app.database.repository_modules.searches import (
    clear_search_history,
    get_search_history,
    get_search_query_by_id,
    save_search,
)
from app.database.repository_modules.tracks import (
    get_track_by_deezer_id,
    get_tracks_by_artist,
    save_track,
)
from app.database.repository_modules.users import (
    get_last_track_id,
    get_user_id,
    get_user_language,
    save_last_track_id,
    set_user_language,
    upsert_user,
)

__all__ = [
    "upsert_user",
    "get_user_id",
    "get_user_language",
    "set_user_language",
    "save_last_track_id",
    "get_last_track_id",
    "save_search",
    "get_search_history",
    "get_search_query_by_id",
    "clear_search_history",
    "save_track",
    "get_track_by_deezer_id",
    "get_tracks_by_artist",
    "add_favorite",
    "remove_favorite",
    "clear_favorites",
    "is_track_favorite",
    "get_favorite_tracks",
    "save_error",
    "get_recent_errors",
    "clear_errors",
    "get_database_summary",
    "cleanup_old_errors",
    "cleanup_search_history",
    "get_cached_search",
    "save_search_cache",
]
