"""
Backward-compatible message constants.

New multi-language code should use:
    from app.localization.translations import t
"""

from app.localization.translations import t


WELCOME_TEXT = t("welcome", "en")
HELP_TEXT = t("help", "en")
ASK_MUSIC_TEXT = t("ask_music", "en")
NO_RESULTS_TEXT = t("no_results", "en")
FAVORITES_EMPTY_TEXT = t("favorites_empty", "en")
HISTORY_EMPTY_TEXT = t("history_empty", "en")
FAVORITE_ADDED_TEXT = t("favorite_added", "en")
FAVORITE_REMOVED_TEXT = t("favorite_removed", "en")
LYRICS_NOT_FOUND_TEXT = t("lyrics_not_found", "en")
GENIUS_ERROR_TEXT = t("genius_error", "en")
BACK_TO_MENU_TEXT = t("btn_main_menu", "en")
MAIN_MENU_TEXT = t("main_menu", "en")
SEARCH_MODE_TEXT = t("search_mode", "en")
MENU_BUTTONS_DISABLED_TEXT = t("menu_buttons_disabled", "en")
BACK_TO_RESULTS_EMPTY_TEXT = t("back_to_results_empty", "en")
HISTORY_CLEAR_CONFIRM_TEXT = t("history_clear_confirm", "en")
HISTORY_CLEARED_TEXT = t("history_cleared", "en")
FAVORITES_CLEAR_CONFIRM_TEXT = t("favorites_clear_confirm", "en")
FAVORITES_CLEARED_TEXT = t("favorites_cleared", "en")
