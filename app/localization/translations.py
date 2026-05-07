"""
Translation layer for visible bot texts.

Callback data remains language-independent. Only user-facing text is translated.
"""

from app.localization.languages import DEFAULT_LANGUAGE


TRANSLATIONS = {
    "en": {
        "btn_spotify": "🟢 Spotify",
        "btn_deezer": "🎧 Deezer",
        "btn_back_results": "⬅️ Back to results",
        "btn_lyrics": "📖 Lyrics",
        "btn_add_favorites": "⭐ Add to favorites",
        "btn_remove_favorites": "❌ Remove from favorites",
        "btn_search_again": "🔎 Search again",
        "btn_music": "🎵 Music",
        "btn_favorites": "⭐ Favorites",
        "btn_history": "🕘 History",
        "btn_language": "🌐 Language",
        "btn_main_menu": "⬅️ Main menu",
        "welcome": "🎧 Welcome to Music Finder Bot!\n\nI can help you find songs, artists, albums and Deezer/Spotify links.",
        "help": "Available commands:\n\n/start - Start bot\n/help - Show help\n/language - Change language\n/version - Show bot version\n/favorites - Show saved tracks\n/history - Show search history",
        "main_menu": "Main menu:",
        "ask_music": "Please, send name of music:",
        "search_mode": "You are now in music search mode.\nSend a song name or press ⬅️ Main menu.",
        "menu_buttons_disabled": "Menu buttons are available only in the main menu.\nPress ⬅️ Main menu first.",
        "no_results": "No results found. Please, try another name.",
        "favorites_empty": "You do not have favorite tracks yet.",
        "history_empty": "Your search history is empty.",
        "favorite_added": "⭐ Track added to favorites.",
        "favorite_removed": "❌ Track removed from favorites.",
        "lyrics_not_found": "Lyrics page was not found.",
        "genius_error": "Could not get lyrics information right now. Please try again later.",
        "back_to_results_empty": "Search results are not available anymore. Please start a new search.",
        "history_clear_confirm": "Are you sure you want to clear your search history?",
        "history_cleared": "🗑 Search history cleared.",
        "favorites_clear_confirm": "Are you sure you want to remove all favorite tracks?",
        "favorites_cleared": "🗑 Favorites cleared.",
        "choose_language": "Choose your language:",
        "language_changed": "Language changed to English.",
        "unsupported_language": "Unsupported language.",
        "favorites_menu": "Favorites menu:",
        "history_menu": "History menu:",
        "favorites_title": "⭐ Your favorite tracks: {count}\n\nClick a track to open its card:",
        "history_title": "🕘 Your recent searches: {count}\n\nClick a query to search again:",
        "search_found": "Found {count} tracks for: {query}",
        "search_query_empty": "Search query cannot be empty.",
        "please_send_text": "Please send text.",
        "something_wrong_searching": "Something went wrong while searching. Please try again.",
        "could_not_load_favorites": "Could not load favorites.",
        "could_not_load_history": "Could not load history.",
        "could_not_load_track": "Could not load track information.",
        "could_not_repeat_search": "Could not repeat this search.",
        "history_item_not_found": "History item was not found.",
        "searching_again": "Searching again...",
        "searching_lyrics": "Searching lyrics...",
        "lyrics_page_found": "Lyrics page found:",
        "admin_only": "This command is available only for the bot admin.",
        "errors_empty": "✅ No saved errors.",
        "errors_header": "⚠️ Recent errors:\n",
        "errors_cleared": "✅ Saved errors cleared.",
        "cancelled": "Cancelled.",
        "could_not_cancel": "Could not cancel.",
        "could_not_clear_history": "Could not clear history.",
        "could_not_clear_favorites": "Could not clear favorites.",
        "could_not_open_confirmation": "Could not open confirmation.",
        "unknown_action": "Unknown action.",
        "search_session_expired": "Search session expired. Please search again.",
        "could_not_change_page": "Could not change page.",
        "could_not_return_results": "Could not return to results.",
        "btn_clear_history": "🗑 Clear history",
        "btn_clear_favorites": "🗑 Clear favorites",
        "btn_yes_clear": "✅ Yes, clear",
        "btn_cancel": "❌ Cancel",
    },
}


_LANGUAGE_OVERRIDES = {
    "uk": {
        "btn_music": "🎵 Музика",
        "btn_favorites": "⭐ Улюблені",
        "btn_history": "🕘 Історія",
        "btn_language": "🌐 Мова",
        "btn_main_menu": "⬅️ Головне меню",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Головне меню:",
        "ask_music": "Напиши назву пісні:",
        "choose_language": "Обери мову:",
        "language_changed": "Мову змінено на українську.",
    },
    "no": {
        "btn_music": "🎵 Musikk",
        "btn_favorites": "⭐ Favoritter",
        "btn_history": "🕘 Historikk",
        "btn_language": "🌐 Språk",
        "btn_main_menu": "⬅️ Hovedmeny",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Hovedmeny:",
        "ask_music": "Send navn på sang:",
        "choose_language": "Velg språk:",
        "language_changed": "Språket er endret til norsk.",
    },
    "de": {
        "btn_music": "🎵 Musik",
        "btn_favorites": "⭐ Favoriten",
        "btn_history": "🕘 Verlauf",
        "btn_language": "🌐 Sprache",
        "btn_main_menu": "⬅️ Hauptmenü",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Hauptmenü:",
        "ask_music": "Sende den Namen eines Songs:",
        "choose_language": "Wähle deine Sprache:",
        "language_changed": "Sprache wurde auf Deutsch geändert.",
    },
    "fr": {
        "btn_music": "🎵 Musique",
        "btn_favorites": "⭐ Favoris",
        "btn_history": "🕘 Historique",
        "btn_language": "🌐 Langue",
        "btn_main_menu": "⬅️ Menu principal",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Menu principal:",
        "ask_music": "Envoie le nom d’une chanson:",
        "choose_language": "Choisis ta langue:",
        "language_changed": "La langue est passée au français.",
    },
    "es": {
        "btn_music": "🎵 Música",
        "btn_favorites": "⭐ Favoritos",
        "btn_history": "🕘 Historial",
        "btn_language": "🌐 Idioma",
        "btn_main_menu": "⬅️ Menú principal",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Menú principal:",
        "ask_music": "Envía el nombre de una canción:",
        "choose_language": "Elige tu idioma:",
        "language_changed": "Idioma cambiado a español.",
    },
    "it": {
        "btn_music": "🎵 Musica",
        "btn_favorites": "⭐ Preferiti",
        "btn_history": "🕘 Cronologia",
        "btn_language": "🌐 Lingua",
        "btn_main_menu": "⬅️ Menu principale",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Menu principale:",
        "ask_music": "Invia il nome di una canzone:",
        "choose_language": "Scegli la lingua:",
        "language_changed": "Lingua cambiata in italiano.",
    },
    "pl": {
        "btn_music": "🎵 Muzyka",
        "btn_favorites": "⭐ Ulubione",
        "btn_history": "🕘 Historia",
        "btn_language": "🌐 Język",
        "btn_main_menu": "⬅️ Menu główne",
        "btn_spotify": "🟢 Spotify",
        "main_menu": "Menu główne:",
        "ask_music": "Wyślij nazwę piosenki:",
        "choose_language": "Wybierz język:",
        "language_changed": "Język zmieniono na polski.",
    },
}

for language_code, overrides in _LANGUAGE_OVERRIDES.items():
    TRANSLATIONS[language_code] = TRANSLATIONS["en"] | overrides


def t(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Returns translated text by key.
    Falls back to English if key or language is missing.
    """
    language_pack = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = language_pack.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))

    if kwargs:
        return text.format(**kwargs)

    return text


def get_menu_action_by_text(text: str) -> str | None:
    """
    Detects bottom menu action by translated button text.
    """
    normalized = text.strip().lower()

    actions = {
        "btn_music": "music",
        "btn_favorites": "favorites",
        "btn_history": "history",
        "btn_language": "language",
        "btn_main_menu": "main_menu",
    }

    for language in TRANSLATIONS:
        for key, action in actions.items():
            if normalized == t(key, language).lower():
                return action

    return None
