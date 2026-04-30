import telebot

from app.bot.context import (
    get_current_page,
    get_page_tracks,
    get_search_context,
    get_total_pages,
    save_search_context,
)
from app.bot.keyboards import (
    main_menu_keyboard,
    search_mode_keyboard,
    search_results_keyboard,
    track_actions_keyboard,
)
from app.config.settings import settings
from app.database.repositories import (
    get_user_language,
    is_track_favorite,
    save_search,
)
from app.localization.translations import t
from app.services.deezer_service import search_tracks
from app.services.track_formatter import format_track_card
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def user_has_search_context(user_id: int) -> bool:
    """
    Checks if user has stored search results.
    """
    context = get_search_context(user_id)
    return bool(context and context.get("tracks"))


def show_main_menu(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int | None = None,
) -> None:
    """
    Shows main menu and restores main bottom keyboard.
    """
    language = get_user_language(user_id) if user_id else "en"

    bot.send_message(
        chat_id,
        t("main_menu", language),
        reply_markup=main_menu_keyboard(language),
    )


def ask_for_music(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int | None = None,
) -> None:
    """
    Asks user to send a song name and shows only Main menu button.
    """
    language = get_user_language(user_id) if user_id else "en"

    bot.send_message(
        chat_id,
        t("search_mode", language),
        reply_markup=search_mode_keyboard(language),
    )

    sent_msg = bot.send_message(chat_id, t("ask_music", language))

    from app.bot.handlers import process_music_search

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
    """
    language = get_user_language(user_id)
    query = query.strip()

    if not query:
        bot.send_message(chat_id, t("search_query_empty", language))
        ask_for_music(bot, chat_id, user_id)
        return

    if save_to_history:
        save_search(user_id, query)

    tracks = search_tracks(
        query=query,
        limit=settings.MAX_SEARCH_RESULTS,
    )

    if not tracks:
        bot.send_message(chat_id, t("no_results", language))
        ask_for_music(bot, chat_id, user_id)
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
        t("search_found", language, count=len(tracks), query=query),
        reply_markup=markup,
    )


def send_current_results_page(
    bot: telebot.TeleBot,
    chat_id: int,
    user_id: int,
) -> None:
    """
    Sends current saved search results page as a new message.
    """
    language = get_user_language(user_id)
    context = get_search_context(user_id)

    if not context:
        bot.send_message(chat_id, t("back_to_results_empty", language))
        return

    page = get_current_page(user_id)

    total_pages = get_total_pages(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
    )

    page_tracks = get_page_tracks(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
        page=page,
    )

    if not page_tracks:
        bot.send_message(chat_id, t("back_to_results_empty", language))
        return

    markup = search_results_keyboard(
        tracks=page_tracks,
        page=page,
        total_pages=total_pages,
    )

    query = context.get("query", "")
    total_tracks = len(context.get("tracks", []))

    bot.send_message(
        chat_id,
        t("search_found", language, count=total_tracks, query=query),
        reply_markup=markup,
    )


def send_track_card(
    bot: telebot.TeleBot,
    chat_id: int,
    telegram_id: int,
    track: dict,
) -> None:
    """
    Sends selected track information with album cover and action buttons.
    """
    language = get_user_language(telegram_id)
    text = format_track_card(track)

    is_favorite = is_track_favorite(
        telegram_id=telegram_id,
        deezer_track_id=track["deezer_track_id"],
    )

    markup = track_actions_keyboard(
        track,
        is_favorite=is_favorite,
        show_back_to_results=user_has_search_context(telegram_id),
        language=language,
    )

    cover_url = track.get("cover_url")

    if cover_url:
        try:
            bot.send_photo(
                chat_id=chat_id,
                photo=cover_url,
                caption=text,
                reply_markup=markup,
            )
            return
        except Exception as error:
            logger.warning("Could not send cover image: %s", error)

    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=markup,
    )
