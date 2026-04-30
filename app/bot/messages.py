from app.bot.constants import BTN_MAIN_MENU


WELCOME_TEXT = (
    "🎧 Welcome to Music Finder Bot!\n\n"
    "I can help you find songs, artists, albums and Deezer links.\n\n"
    "Press music or just send me a song name."
)

HELP_TEXT = (
    "Available commands:\n\n"
    "/start - Start bot\n"
    "/help - Show help\n"
    "/version - Show bot version\n"
    "/favorites - Show saved tracks\n"
    "/history - Show search history\n"
    "/errors - Show recent saved errors (admin only)\n"
    "/clear_errors - Clear saved errors (admin only)\n\n"
    "You can also send a song name directly."
)

ASK_MUSIC_TEXT = "Please, send name of music:"

NO_RESULTS_TEXT = "No results found. Please, try another name."

FAVORITES_EMPTY_TEXT = "You do not have favorite tracks yet."

HISTORY_EMPTY_TEXT = "Your search history is empty."

FAVORITE_ADDED_TEXT = "⭐ Track added to favorites."

FAVORITE_REMOVED_TEXT = "❌ Track removed from favorites."

LYRICS_NOT_FOUND_TEXT = "Lyrics page was not found."

GENIUS_ERROR_TEXT = (
    "Could not get lyrics information right now. "
    "Please try again later."
)

BACK_TO_MENU_TEXT = BTN_MAIN_MENU

MAIN_MENU_TEXT = "Main menu:"

SEARCH_MODE_TEXT = (
    "You are now in music search mode.\n"
    "Send a song name or press ⬅️ Main menu."
)

MENU_BUTTONS_DISABLED_TEXT = (
    "Menu buttons are available only in the main menu.\n"
    "Press ⬅️ Main menu first."
)

BACK_TO_RESULTS_EMPTY_TEXT = (
    "Search results are not available anymore. "
    "Please start a new search."
)

HISTORY_CLEAR_CONFIRM_TEXT = (
    "Are you sure you want to clear your search history?"
)

HISTORY_CLEARED_TEXT = "🗑 Search history cleared."

FAVORITES_CLEAR_CONFIRM_TEXT = (
    "Are you sure you want to remove all favorite tracks?"
)

FAVORITES_CLEARED_TEXT = "🗑 Favorites cleared."
