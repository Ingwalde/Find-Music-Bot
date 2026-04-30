"""
Centralized Telegram button texts and callback constants.

Keeping these values in one file prevents typos and duplicated strings
across handlers, callbacks and keyboard builders.
"""

# Technical actions
ACTION_MUSIC = "music"
ACTION_FAVORITES = "favorites"
ACTION_HISTORY = "history"
ACTION_LANGUAGE = "language"
ACTION_MAIN_MENU_TEXT = "main_menu"

# Universal bottom keyboard button
BTN_LANGUAGE = "🌐 Language"

# Callback prefixes
CB_TRACK = "track"
CB_PAGE = "page"
CB_FAVORITE = "fav"
CB_UNFAVORITE = "unfav"
CB_LYRICS = "lyrics"
CB_HISTORY = "hist"
CB_LANGUAGE = "lang"

# Callback actions
ACTION_BACK_RESULTS = "back_results"
ACTION_SEARCH_AGAIN = "search_again"
ACTION_MAIN_MENU = "main_menu"
ACTION_NOOP = "noop"

ACTION_HISTORY_CLEAR_REQUEST = "history_clear_request"
ACTION_HISTORY_CLEAR_CONFIRM = "history_clear_confirm"
ACTION_HISTORY_CLEAR_CANCEL = "history_clear_cancel"

ACTION_FAVORITES_CLEAR_REQUEST = "favorites_clear_request"
ACTION_FAVORITES_CLEAR_CONFIRM = "favorites_clear_confirm"
ACTION_FAVORITES_CLEAR_CANCEL = "favorites_clear_cancel"


def make_callback(prefix: str, value: str | int) -> str:
    """
    Creates callback_data in a consistent format.
    """
    return f"{prefix}:{value}"
