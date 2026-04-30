"""
Translation layer for visible bot texts.

Callback data remains language-independent. Only user-facing text is translated.
"""

from app.localization.languages import DEFAULT_LANGUAGE


BASE_EN = {
    "welcome": (
        "🎧 Welcome to Music Finder Bot!\n\n"
        "I can help you find songs, artists, albums and Deezer links.\n\n"
        "Press music or just send me a song name."
    ),
    "help": (
        "Available commands:\n\n"
        "/start - Start bot\n"
        "/help - Show help\n"
        "/language - Change language\n"
        "/version - Show bot version\n"
        "/favorites - Show saved tracks\n"
        "/history - Show search history\n"
        "/errors - Show recent saved errors (admin only)\n"
        "/clear_errors - Clear saved errors (admin only)\n\n"
        "You can also send a song name directly."
    ),
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
    "btn_music": "music",
    "btn_favorites": "favorites",
    "btn_history": "history",
    "btn_main_menu": "⬅️ Main menu",
    "btn_deezer": "🎧 Deezer",
    "btn_back_results": "⬅️ Back to results",
    "btn_lyrics": "📖 Lyrics",
    "btn_add_favorites": "⭐ Add to favorites",
    "btn_remove_favorites": "❌ Remove from favorites",
    "btn_search_again": "🔎 Search again",
    "btn_clear_history": "🗑 Clear history",
    "btn_clear_favorites": "🗑 Clear favorites",
    "btn_yes_clear": "✅ Yes, clear",
    "btn_cancel": "❌ Cancel",
}

TRANSLATIONS = {
    "en": BASE_EN,
    "uk": {
        **BASE_EN,
        "welcome": "🎧 Вітаю у Music Finder Bot!\n\nЯ допоможу знайти пісні, артистів, альбоми та посилання Deezer.\n\nНатисни music або просто напиши назву пісні.",
        "help": "Доступні команди:\n\n/start - Запустити бота\n/help - Допомога\n/language - Змінити мову\n/version - Версія бота\n/favorites - Улюблені треки\n/history - Історія пошуку\n/errors - Останні помилки (тільки admin)\n/clear_errors - Очистити помилки (тільки admin)\n\nТакож можна просто написати назву пісні.",
        "main_menu": "Головне меню:",
        "ask_music": "Напиши назву пісні:",
        "search_mode": "Ти зараз у режимі пошуку музики.\nНапиши назву пісні або натисни ⬅️ Головне меню.",
        "menu_buttons_disabled": "Кнопки меню доступні тільки в головному меню.\nСпочатку натисни ⬅️ Головне меню.",
        "no_results": "Нічого не знайдено. Спробуй іншу назву.",
        "favorites_empty": "У тебе ще немає улюблених треків.",
        "history_empty": "Історія пошуку порожня.",
        "favorite_added": "⭐ Трек додано до улюблених.",
        "favorite_removed": "❌ Трек видалено з улюблених.",
        "lyrics_not_found": "Сторінку з lyrics не знайдено.",
        "genius_error": "Зараз не вдалося отримати lyrics. Спробуй пізніше.",
        "back_to_results_empty": "Результати пошуку вже недоступні. Почни новий пошук.",
        "history_clear_confirm": "Точно очистити історію пошуку?",
        "history_cleared": "🗑 Історію пошуку очищено.",
        "favorites_clear_confirm": "Точно видалити всі улюблені треки?",
        "favorites_cleared": "🗑 Улюблені очищено.",
        "choose_language": "Обери мову:",
        "language_changed": "Мову змінено на українську.",
        "favorites_menu": "Меню улюблених:",
        "history_menu": "Меню історії:",
        "favorites_title": "⭐ Улюблені треки: {count}\n\nНатисни на трек, щоб відкрити картку:",
        "history_title": "🕘 Останні пошуки: {count}\n\nНатисни на запит, щоб повторити пошук:",
        "search_found": "Знайдено {count} треків для: {query}",
        "btn_favorites": "улюблені",
        "btn_history": "історія",
        "btn_main_menu": "⬅️ Головне меню",
        "btn_back_results": "⬅️ До результатів",
        "btn_add_favorites": "⭐ Додати до улюблених",
        "btn_remove_favorites": "❌ Видалити з улюблених",
        "btn_search_again": "🔎 Шукати ще",
        "btn_clear_history": "🗑 Очистити історію",
        "btn_clear_favorites": "🗑 Очистити улюблені",
        "btn_yes_clear": "✅ Так, очистити",
        "btn_cancel": "❌ Скасувати",
    },
    "no": {
        **BASE_EN,
        "welcome": "🎧 Velkommen til Music Finder Bot!\n\nJeg kan hjelpe deg å finne sanger, artister, album og Deezer-lenker.\n\nTrykk music eller send et sangnavn.",
        "help": "Tilgjengelige kommandoer:\n\n/start - Start bot\n/help - Hjelp\n/language - Endre språk\n/version - Vis versjon\n/favorites - Favoritter\n/history - Søkehistorikk",
        "main_menu": "Hovedmeny:",
        "ask_music": "Send navn på sang:",
        "search_mode": "Du er nå i musikksøk.\nSend et sangnavn eller trykk ⬅️ Hovedmeny.",
        "no_results": "Ingen resultater funnet. Prøv et annet navn.",
        "favorites_empty": "Du har ingen favorittsanger ennå.",
        "history_empty": "Søkehistorikken er tom.",
        "favorite_added": "⭐ Lagt til i favoritter.",
        "favorite_removed": "❌ Fjernet fra favoritter.",
        "choose_language": "Velg språk:",
        "language_changed": "Språket er endret til norsk.",
        "favorites_menu": "Favorittmeny:",
        "history_menu": "Historikkmeny:",
        "favorites_title": "⭐ Dine favoritter: {count}\n\nTrykk på en sang for å åpne kortet:",
        "history_title": "🕘 Siste søk: {count}\n\nTrykk på et søk for å søke igjen:",
        "search_found": "Fant {count} sanger for: {query}",
        "btn_favorites": "favoritter",
        "btn_history": "historikk",
        "btn_main_menu": "⬅️ Hovedmeny",
    },
    "de": {
        **BASE_EN,
        "welcome": "🎧 Willkommen beim Music Finder Bot!\n\nIch helfe dir, Songs, Künstler, Alben und Deezer-Links zu finden.\n\nDrücke music oder sende einen Songnamen.",
        "main_menu": "Hauptmenü:",
        "ask_music": "Sende den Namen eines Songs:",
        "search_mode": "Du bist jetzt im Musik-Suchmodus.\nSende einen Songnamen oder drücke ⬅️ Hauptmenü.",
        "no_results": "Keine Ergebnisse gefunden. Versuche einen anderen Namen.",
        "favorites_empty": "Du hast noch keine Favoriten.",
        "history_empty": "Dein Suchverlauf ist leer.",
        "favorite_added": "⭐ Zu Favoriten hinzugefügt.",
        "favorite_removed": "❌ Aus Favoriten entfernt.",
        "choose_language": "Wähle deine Sprache:",
        "language_changed": "Sprache wurde auf Deutsch geändert.",
        "favorites_menu": "Favoritenmenü:",
        "history_menu": "Suchverlauf:",
        "search_found": "{count} Tracks gefunden für: {query}",
        "btn_favorites": "favoriten",
        "btn_history": "verlauf",
        "btn_main_menu": "⬅️ Hauptmenü",
    },
    "fr": {
        **BASE_EN,
        "welcome": "🎧 Bienvenue dans Music Finder Bot!\n\nJe peux t’aider à trouver des chansons, artistes, albums et liens Deezer.\n\nAppuie sur music ou envoie le nom d’une chanson.",
        "main_menu": "Menu principal:",
        "ask_music": "Envoie le nom d’une chanson:",
        "search_mode": "Tu es en mode recherche musicale.\nEnvoie une chanson ou appuie sur ⬅️ Menu principal.",
        "no_results": "Aucun résultat trouvé. Essaie un autre nom.",
        "favorites_empty": "Tu n’as pas encore de favoris.",
        "history_empty": "Ton historique est vide.",
        "favorite_added": "⭐ Ajouté aux favoris.",
        "favorite_removed": "❌ Retiré des favoris.",
        "choose_language": "Choisis ta langue:",
        "language_changed": "La langue est passée au français.",
        "favorites_menu": "Menu des favoris:",
        "history_menu": "Menu historique:",
        "search_found": "{count} titres trouvés pour: {query}",
        "btn_favorites": "favoris",
        "btn_history": "historique",
        "btn_main_menu": "⬅️ Menu principal",
    },
    "es": {
        **BASE_EN,
        "welcome": "🎧 ¡Bienvenido a Music Finder Bot!\n\nPuedo ayudarte a encontrar canciones, artistas, álbumes y enlaces de Deezer.\n\nPulsa music o envía el nombre de una canción.",
        "main_menu": "Menú principal:",
        "ask_music": "Envía el nombre de una canción:",
        "search_mode": "Estás en modo de búsqueda musical.\nEnvía una canción o pulsa ⬅️ Menú principal.",
        "no_results": "No se encontraron resultados. Prueba otro nombre.",
        "favorites_empty": "Aún no tienes canciones favoritas.",
        "history_empty": "Tu historial está vacío.",
        "favorite_added": "⭐ Añadido a favoritos.",
        "favorite_removed": "❌ Eliminado de favoritos.",
        "choose_language": "Elige tu idioma:",
        "language_changed": "Idioma cambiado a español.",
        "favorites_menu": "Menú de favoritos:",
        "history_menu": "Menú de historial:",
        "search_found": "Encontrados {count} temas para: {query}",
        "btn_favorites": "favoritos",
        "btn_history": "historial",
        "btn_main_menu": "⬅️ Menú principal",
    },
    "it": {
        **BASE_EN,
        "welcome": "🎧 Benvenuto in Music Finder Bot!\n\nPosso aiutarti a trovare brani, artisti, album e link Deezer.\n\nPremi music o invia il nome di una canzone.",
        "main_menu": "Menu principale:",
        "ask_music": "Invia il nome di una canzone:",
        "search_mode": "Sei in modalità ricerca musicale.\nInvia una canzone o premi ⬅️ Menu principale.",
        "no_results": "Nessun risultato trovato. Prova un altro nome.",
        "favorites_empty": "Non hai ancora brani preferiti.",
        "history_empty": "La cronologia è vuota.",
        "favorite_added": "⭐ Aggiunto ai preferiti.",
        "favorite_removed": "❌ Rimosso dai preferiti.",
        "choose_language": "Scegli la lingua:",
        "language_changed": "Lingua cambiata in italiano.",
        "favorites_menu": "Menu preferiti:",
        "history_menu": "Menu cronologia:",
        "search_found": "Trovati {count} brani per: {query}",
        "btn_favorites": "preferiti",
        "btn_history": "cronologia",
        "btn_main_menu": "⬅️ Menu principale",
    },
    "pl": {
        **BASE_EN,
        "welcome": "🎧 Witaj w Music Finder Bot!\n\nPomogę znaleźć piosenki, artystów, albumy i linki Deezer.\n\nNaciśnij music albo wyślij nazwę piosenki.",
        "main_menu": "Menu główne:",
        "ask_music": "Wyślij nazwę piosenki:",
        "search_mode": "Jesteś w trybie wyszukiwania muzyki.\nWyślij nazwę piosenki albo naciśnij ⬅️ Menu główne.",
        "no_results": "Nie znaleziono wyników. Spróbuj innej nazwy.",
        "favorites_empty": "Nie masz jeszcze ulubionych utworów.",
        "history_empty": "Historia wyszukiwania jest pusta.",
        "favorite_added": "⭐ Dodano do ulubionych.",
        "favorite_removed": "❌ Usunięto z ulubionych.",
        "choose_language": "Wybierz język:",
        "language_changed": "Język zmieniono na polski.",
        "favorites_menu": "Menu ulubionych:",
        "history_menu": "Menu historii:",
        "search_found": "Znaleziono {count} utworów dla: {query}",
        "btn_favorites": "ulubione",
        "btn_history": "historia",
        "btn_main_menu": "⬅️ Menu główne",
    },
}


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
        "btn_main_menu": "main_menu",
    }

    for language in TRANSLATIONS:
        for key, action in actions.items():
            if normalized == t(key, language).lower():
                return action

    return None
