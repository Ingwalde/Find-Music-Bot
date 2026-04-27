import telebot
from telebot import types

from app.bot.keyboards import (
    main_menu_keyboard,
    search_mode_keyboard,
    search_results_keyboard,
    favorites_keyboard,
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
from app.bot.states import (
    MAIN_MENU,
    SEARCH_MODE,
    set_user_state,
    get_user_state,
    is_main_menu,
)
from app.config.settings import settings
from app.database.repositories import (
    upsert_user,
    save_search,
    get_favorite_tracks,
    get_search_history,
)
from app.services.deezer_service import search_tracks
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def ask_for_music(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int
) -> None:
    """
    Asks user to send a song name and switches user to search mode.
    """
    set_user_state(user_id, SEARCH_MODE)

    bot.send_message(
        chat_id,
        SEARCH_MODE_TEXT,
        reply_markup=search_mode_keyboard()
    )

    sent_msg = bot.send_message(chat_id, ASK_MUSIC_TEXT)

    bot.register_next_step_handler(
        sent_msg,
        lambda message: process_music_search(bot, message)
    )


def process_music_search(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Processes user's song search query.
    """
    if not message.text:
        bot.send_message(message.chat.id, "Please send text.")
        ask_for_music(bot, message.chat.id, message.from_user.id)
        return

    text = message.text.strip()
    text_lower = text.lower()

    if text == BACK_TO_MENU_TEXT:
        show_main_menu(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        return

    if text == "/start":
        set_user_state(message.from_user.id, MAIN_MENU)
        bot.send_message(
            message.chat.id,
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard()
        )
        return

    if text_lower in ["music", "favorites", "history"]:
        bot.send_message(
            message.chat.id,
            MENU_BUTTONS_DISABLED_TEXT,
            reply_markup=search_mode_keyboard()
        )

        sent_msg = bot.send_message(message.chat.id, ASK_MUSIC_TEXT)
        bot.register_next_step_handler(
            sent_msg,
            lambda next_message: process_music_search(bot, next_message)
        )
        return

    query = text

    if not query:
        bot.send_message(message.chat.id, "Search query cannot be empty.")
        ask_for_music(bot, message.chat.id, message.from_user.id)
        return

    try:
        upsert_user(message.from_user)
        save_search(message.from_user.id, query)

        tracks = search_tracks(
            query=query,
            limit=settings.MAX_SEARCH_RESULTS
        )

        if not tracks:
            bot.send_message(message.chat.id, NO_RESULTS_TEXT)
            ask_for_music(bot, message.chat.id, message.from_user.id)
            return

        markup = search_results_keyboard(tracks)

        bot.send_message(
            message.chat.id,
            f"Found {len(tracks)} tracks for: {query}",
            reply_markup=markup
        )

    except Exception as error:
        logger.exception("Search error: %s", error)
        bot.send_message(
            message.chat.id,
            "Something went wrong while searching. Please try again."
        )

def show_main_menu(bot: telebot.TeleBot, chat_id: int, user_id: int) -> None:
    """
    Returns user to main menu and enables main menu buttons.
    """
    set_user_state(user_id, MAIN_MENU)

    bot.send_message(
        chat_id,
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard()
    )

def show_favorites(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's favorite tracks.
    """
    upsert_user(message.from_user)

    tracks = get_favorite_tracks(message.from_user.id)

    if not tracks:
        bot.send_message(message.chat.id, FAVORITES_EMPTY_TEXT)
        return

    markup = favorites_keyboard(tracks)

    bot.send_message(
        message.chat.id,
        "⭐ Your favorite tracks:",
        reply_markup=markup,
    )


def show_history(bot: telebot.TeleBot, message: types.Message) -> None:
    """
    Shows user's recent search history.
    """
    upsert_user(message.from_user)

    history = get_search_history(message.from_user.id, limit=10)

    if not history:
        bot.send_message(message.chat.id, HISTORY_EMPTY_TEXT)
        return

    lines = ["🕘 Your recent searches:\n"]

    for index, item in enumerate(history, start=1):
        lines.append(f"{index}. {item['query']}")

    bot.send_message(message.chat.id, "\n".join(lines))


def register_handlers(bot: telebot.TeleBot) -> None:
    """
    Registers all message handlers.
    """

    @bot.message_handler(commands=["start"])
    def start_handler(message: types.Message) -> None:
        upsert_user(message.from_user)
        set_user_state(message.from_user.id, MAIN_MENU)

        bot.send_message(
            message.chat.id,
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard()
        )

    @bot.message_handler(commands=["help"])
    def help_handler(message: types.Message) -> None:
        bot.send_message(message.chat.id, HELP_TEXT)

    @bot.message_handler(commands=["favorites"])
    def favorites_handler(message: types.Message) -> None:
        set_user_state(message.from_user.id, MAIN_MENU)
        show_favorites(bot, message)


    @bot.message_handler(commands=["history"])
    def history_handler(message: types.Message) -> None:
        set_user_state(message.from_user.id, MAIN_MENU)
        show_history(bot, message)

    @bot.message_handler(content_types=["text"])
    def text_handler(message: types.Message) -> None:
        text = message.text.strip()
        text_lower = text.lower()

        current_state = get_user_state(message.from_user.id)

        if text == BACK_TO_MENU_TEXT:
            show_main_menu(
                bot=bot,
                chat_id=message.chat.id,
                user_id=message.from_user.id
            )
            return

        if text_lower in ["music", "favorites", "history"]:
            if current_state != MAIN_MENU:
                bot.send_message(
                    message.chat.id,
                    MENU_BUTTONS_DISABLED_TEXT,
                    reply_markup=search_mode_keyboard()
                )
                return

            if text_lower == "music":
                ask_for_music(bot, message.chat.id, message.from_user.id)
                return

            if text_lower == "favorites":
                show_favorites(bot, message)
                return

            if text_lower == "history":
                show_history(bot, message)
                return

        process_music_search(bot, message)
