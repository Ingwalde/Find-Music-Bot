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
    get_schema_version,
    get_table_counts,
)
from app.database.repository_modules.common import row_to_dict
from app.database.repository_modules.errors import clear_errors, get_recent_errors, save_error
from app.database.repository_modules.favorites import (
    add_favorite,
    clear_favorites,
    get_favorite_tracks,
    is_track_favorite,
    remove_favorite,
)
from app.database.repository_modules.searches import (
    clear_search_history,
    get_search_history,
    get_search_query_by_id,
    save_search,
    trim_search_history,
)
from app.database.repository_modules.tracks import get_track_by_deezer_id, save_track
from app.database.repository_modules.users import (
    get_user_id,
    get_user_language,
    set_user_language,
    upsert_user,
)

__all__ = [
    "row_to_dict",
    "upsert_user",
    "get_user_id",
    "get_user_language",
    "set_user_language",
    "trim_search_history",
    "save_search",
    "get_search_history",
    "get_search_query_by_id",
    "clear_search_history",
    "save_track",
    "get_track_by_deezer_id",
    "add_favorite",
    "remove_favorite",
    "clear_favorites",
    "is_track_favorite",
    "get_favorite_tracks",
    "save_error",
    "get_recent_errors",
    "clear_errors",
    "get_table_counts",
    "get_database_summary",
    "get_schema_version",
    "cleanup_old_errors",
    "cleanup_search_history",
]
