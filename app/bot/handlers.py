import telebot
from telebot import types

from app.bot.context import (
    get_page_tracks,
    get_total_pages,
    save_search_context,
)
from app.bot.keyboards import (
    main_menu_keyboard,
    search_mode_keyboard,
    search_results_keyboard,
    favorites_keyboard,
    history_keyboard,
)
from app.bot.messages import (
    WELCOME_TEXT,
    HELP_TEXT,
    ASK_MUSIC_TEXT,
    NO_RESULTS_TEXT,
    FAVORITES_EMPTY_TEXT,
    HISTORY_EMPTY_TEXT,
    BACK_TO_MENU_TEXT,
    MAIN_MENU_TEXT,
    SEARCH_MODE_TEXT,
    MENU_BUTTONS_DISABLED_TEXT,
)
from app.config.settings import settings
from app.database.repositories import (
    upsert_user,
    save_search,
    get_favorite_tracks,
    get_search_history,
    get_recent_errors,
    clear_errors,
)
from app.services.deezer_service import search_tracks
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.version import __version__


logger = setup_logger(__name__)


def is_admin(user_id: int) -> bool:
    """
    Checks whether user can access admin-only commands.
    """
    return settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID


def format_recent_errors() -> str:
    """
    Builds readable message with recent saved errors.
    """
    errors = get_recent_errors(limit=settings.ERROR_HISTORY_LIMIT)

    if not errors:
        return "✅ No saved errors."

    lines = ["⚠️ Recent errors:\n"]

    for index, item in enumerate(errors, start=1):
        source = item.get("source", "unknown")
        created_at = item.get("created_at", "unknown time")
        error_message = item.get("error_message", "Unknown error")
        telegram_id = item.get("telegram_id")

        user_part = f" | user: {telegram_id}" if telegram_id else ""
        lines.append(
            f"{index}. [{created_at}] {source}{user_part}\n"
            f"   {error_message}"
        )

    return "\n".join(lines)


def show_main_menu(bot: telebot.TeleBot, chat_id: int) -> None:
    """
    Shows main menu and restores main bottom keyboard.
    """
    bot.send_message(
        chat_id,
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
    )


def ask_for_music(bot: telebot.TeleBot, chat_id: int) -> None:
    """
    Asks user to send a song name and shows only Main menu button.
    """
    bot.send_message(
        chat_id,
        SEARCH_MODE_TEXT,
        reply_markup=search_mode_keyboard(),
    )

    sent_msg = bot.send_message(chat_id, ASK_MUSIC_TEXT)
    bot.register_next_step_handler(
        sent_msg,
        lambda message: process_music_search(bot, message),
    )


def send_search_results(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int,
    query: str,
    save_to_history: bool = True,
) -> None:
    """
    Searches tracks, stores results in user context and sends first page.
    Used by direct search and history callbacks.
    """
    query = query.strip()

    if not query:
        bot.send_message(chat_id, "Search query cannot be empty.")
        ask_for_music(bot, chat_id)
        return

    if save_to_history:
        save_search(user_id, query)

    tracks = search_tracks(
        query=query,
        limit=settings.MAX_SEARCH_RESULTS,
    )

    if not tracks:
        bot.send_message(chat_id, NO_RESULTS_TEXT)
        ask_for_music(bot, chat_id)
        return

    save_search_context(user_id=user_id, query=query, tracks=tracks)

    total_pages = get_total_pages(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
    )

    page_tracks = get_page_tracks(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
        page=0,
    )

    markup = search_results_keyboard(
        tracks=page_tracks,
        page=0,
        total_pages=total_pages,
    )

    bot.send_message(
        chat_id,
        f"Found {len(tracks)} tracks for: {query}",
        reply_markup=markup,
    )


def process_music_search(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Processes user's song search query.
    """
    if not message.text:
        bot.send_message(message.chat.id, "Please send text.")
        ask_for_music(bot, message.chat.id)
        return

    text = message.text.strip()
    text_lower = text.lower()

    if text == BACK_TO_MENU_TEXT:
        show_main_menu(bot, message.chat.id)
        return

    if text == "/start":
        bot.send_message(
            message.chat.id,
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard(),
        )
        return

    if text_lower in ["music", "favorites", "history"]:
        bot.send_message(
            message.chat.id,
            MENU_BUTTONS_DISABLED_TEXT,
            reply_markup=search_mode_keyboard(),
        )
        sent_msg = bot.send_message(message.chat.id, ASK_MUSIC_TEXT)
        bot.register_next_step_handler(
            sent_msg,
            lambda next_message: process_music_search(bot, next_message),
        )
        return

    try:
        upsert_user(message.from_user)
        send_search_results(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            query=text,
            save_to_history=True,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="music_search",
            error=error,
        )
        bot.send_message(
            message.chat.id,
            "Something went wrong while searching. Please try again.",
        )


def show_favorites(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's favorite tracks.
    Main menu button is shown as bottom keyboard.
    """
    try:
        upsert_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "Favorites menu:",
            reply_markup=search_mode_keyboard(),
        )

        tracks = get_favorite_tracks(message.from_user.id)

        if not tracks:
            bot.send_message(message.chat.id, FAVORITES_EMPTY_TEXT)
            return

        markup = favorites_keyboard(tracks)

        bot.send_message(
            message.chat.id,
            f"⭐ Your favorite tracks: {len(tracks)}\n\nClick a track to open its card:",
            reply_markup=markup,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="favorites",
            error=error,
        )
        bot.send_message(message.chat.id, "Could not load favorites.")


def show_history(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's recent unique search history as clickable buttons.
    Main menu button is shown as bottom keyboard.
    """
    try:
        upsert_user(message.from_user)

        bot.send_message(
            message.chat.id,
            "History menu:",
            reply_markup=search_mode_keyboard(),
        )

        history = get_search_history(
            message.from_user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            bot.send_message(message.chat.id, HISTORY_EMPTY_TEXT)
            return

        markup = history_keyboard(history)

        bot.send_message(
            message.chat.id,
            f"🕘 Your recent searches: {len(history)}\n\nClick a query to search again:",
            reply_markup=markup,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="history",
            error=error,
        )
        bot.send_message(message.chat.id, "Could not load history.")


def register_handlers(bot: telebot.TeleBot) -> None:
    """
    Registers all message handlers.
    """

    @bot.message_handler(commands=["start"])
    def start_handler(message: types.Message) -> None:
        upsert_user(message.from_user)

        bot.send_message(
            message.chat.id,
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard(),
        )

    @bot.message_handler(commands=["help"])
    def help_handler(message: types.Message) -> None:
        bot.send_message(message.chat.id, HELP_TEXT)

    @bot.message_handler(commands=["version"])
    def version_handler(message: types.Message) -> None:
        bot.send_message(
            message.chat.id,
            f"🎧 Find Music Bot\nVersion: v{__version__}",
        )

    @bot.message_handler(commands=["errors"])
    def errors_handler(message: types.Message) -> None:
        if not is_admin(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "This command is available only for the bot admin.",
            )
            return

        bot.send_message(message.chat.id, format_recent_errors())

    @bot.message_handler(commands=["clear_errors"])
    def clear_errors_handler(message: types.Message) -> None:
        if not is_admin(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "This command is available only for the bot admin.",
            )
            return

        clear_errors()
        bot.send_message(message.chat.id, "✅ Saved errors cleared.")

    @bot.message_handler(commands=["favorites"])
    def favorites_handler(message: types.Message) -> None:
        show_favorites(bot, message)

    @bot.message_handler(commands=["history"])
    def history_handler(message: types.Message) -> None:
        show_history(bot, message)

    @bot.message_handler(content_types=["text"])
    def text_handler(message: types.Message) -> None:
        text = message.text.strip()
        text_lower = text.lower()

        if text == BACK_TO_MENU_TEXT:
            show_main_menu(bot, message.chat.id)
            return

        if text_lower == "music":
            ask_for_music(bot, message.chat.id)
            return

        if text_lower == "favorites":
            show_favorites(bot, message)
            return

        if text_lower == "history":
            show_history(bot, message)
            return

        process_music_search(bot, message)
