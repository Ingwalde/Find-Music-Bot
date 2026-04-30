import telebot
from telebot import types

from app.bot.actions import ask_for_music, send_search_results, show_main_menu
from app.bot.keyboards import (
    favorites_keyboard,
    history_keyboard,
    language_keyboard,
    main_menu_keyboard,
    search_mode_keyboard,
)
from app.config.settings import settings
from app.database.repositories import (
    clear_errors,
    get_favorite_tracks,
    get_recent_errors,
    get_search_history,
    get_user_language,
    upsert_user,
)
from app.localization.translations import get_menu_action_by_text, t
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.version import __version__


logger = setup_logger(__name__)


def is_admin(user_id: int) -> bool:
    """
    Checks whether user can access admin-only commands.
    """
    return settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID


def format_recent_errors(language: str = "en") -> str:
    """
    Builds readable message with recent saved errors.
    """
    errors = get_recent_errors(limit=settings.ERROR_HISTORY_LIMIT)

    if not errors:
        return t("errors_empty", language)

    lines = [t("errors_header", language)]

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


def process_music_search(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Processes user's song search query.
    """
    upsert_user(message.from_user)
    language = get_user_language(message.from_user.id)

    if not message.text:
        bot.send_message(message.chat.id, t("please_send_text", language))
        ask_for_music(bot, message.chat.id, message.from_user.id)
        return

    text = message.text.strip()
    action = get_menu_action_by_text(text)

    if action == "main_menu":
        show_main_menu(bot, message.chat.id, message.from_user.id)
        return

    if text == "/start":
        bot.send_message(
            message.chat.id,
            t("welcome", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    if action in ["music", "favorites", "history"]:
        bot.send_message(
            message.chat.id,
            t("menu_buttons_disabled", language),
            reply_markup=search_mode_keyboard(language),
        )
        sent_msg = bot.send_message(message.chat.id, t("ask_music", language))
        bot.register_next_step_handler(
            sent_msg,
            lambda next_message: process_music_search(bot, next_message),
        )
        return

    try:
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
        bot.send_message(message.chat.id, t("something_wrong_searching", language))


def show_favorites(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's favorite tracks.
    Main menu button is shown as bottom keyboard.
    """
    try:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        bot.send_message(
            message.chat.id,
            t("favorites_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        tracks = get_favorite_tracks(message.from_user.id)

        if not tracks:
            bot.send_message(message.chat.id, t("favorites_empty", language))
            return

        markup = favorites_keyboard(tracks, language)

        bot.send_message(
            message.chat.id,
            t("favorites_title", language, count=len(tracks)),
            reply_markup=markup,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="favorites",
            error=error,
        )
        language = get_user_language(message.from_user.id)
        bot.send_message(message.chat.id, t("could_not_load_favorites", language))


def show_history(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's recent unique search history as clickable buttons.
    Main menu button is shown as bottom keyboard.
    """
    try:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        bot.send_message(
            message.chat.id,
            t("history_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        history = get_search_history(
            message.from_user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            bot.send_message(message.chat.id, t("history_empty", language))
            return

        markup = history_keyboard(history, language)

        bot.send_message(
            message.chat.id,
            t("history_title", language, count=len(history)),
            reply_markup=markup,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="history",
            error=error,
        )
        language = get_user_language(message.from_user.id)
        bot.send_message(message.chat.id, t("could_not_load_history", language))


def register_handlers(bot: telebot.TeleBot) -> None:
    """
    Registers all message handlers.
    """

    @bot.message_handler(commands=["start"])
    def start_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        bot.send_message(
            message.chat.id,
            t("welcome", language),
            reply_markup=main_menu_keyboard(language),
        )

    @bot.message_handler(commands=["help"])
    def help_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        bot.send_message(message.chat.id, t("help", language))

    @bot.message_handler(commands=["language"])
    def language_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        bot.send_message(
            message.chat.id,
            t("choose_language", language),
            reply_markup=language_keyboard(),
        )

    @bot.message_handler(commands=["version"])
    def version_handler(message: types.Message) -> None:
        bot.send_message(
            message.chat.id,
            f"🎧 Find Music Bot\nVersion: v{__version__}",
        )

    @bot.message_handler(commands=["errors"])
    def errors_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, t("admin_only", language))
            return

        bot.send_message(message.chat.id, format_recent_errors(language))

    @bot.message_handler(commands=["clear_errors"])
    def clear_errors_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        language = get_user_language(message.from_user.id)

        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, t("admin_only", language))
            return

        clear_errors()
        bot.send_message(message.chat.id, t("errors_cleared", language))

    @bot.message_handler(commands=["favorites"])
    def favorites_handler(message: types.Message) -> None:
        show_favorites(bot, message)

    @bot.message_handler(commands=["history"])
    def history_handler(message: types.Message) -> None:
        show_history(bot, message)

    @bot.message_handler(content_types=["text"])
    def text_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        action = get_menu_action_by_text(message.text)

        if action == "main_menu":
            show_main_menu(bot, message.chat.id, message.from_user.id)
            return

        if action == "music":
            ask_for_music(bot, message.chat.id, message.from_user.id)
            return

        if action == "favorites":
            show_favorites(bot, message)
            return

        if action == "history":
            show_history(bot, message)
            return

        process_music_search(bot, message)
