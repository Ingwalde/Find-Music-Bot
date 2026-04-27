import telebot
from telebot import types

from app.bot.context import (
    get_page_tracks,
    get_search_context,
    get_total_pages,
    set_search_page,
)
from app.bot.handlers import ask_for_music, send_search_results
from app.bot.keyboards import (
    track_actions_keyboard,
    genius_url_keyboard,
    search_results_keyboard,
)
from app.bot.messages import (
    FAVORITE_ADDED_TEXT,
    FAVORITE_REMOVED_TEXT,
    LYRICS_NOT_FOUND_TEXT,
    GENIUS_ERROR_TEXT,
    HISTORY_EMPTY_TEXT,
)
from app.config.settings import settings
from app.database.repositories import (
    upsert_user,
    save_track,
    add_favorite,
    remove_favorite,
    is_track_favorite,
    get_search_query_by_id,
    clear_search_history,
)
from app.services.deezer_service import get_track
from app.services.lyrics_service import find_lyrics_url
from app.services.track_formatter import format_track_card
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def send_track_card(
    bot: telebot.TeleBot,
    chat_id: int,
    telegram_id: int,
    track: dict,
) -> None:
    """
    Sends selected track information with album cover and action buttons.
    """
    text = format_track_card(track)

    is_favorite = is_track_favorite(
        telegram_id=telegram_id,
        deezer_track_id=track["deezer_track_id"],
    )

    markup = track_actions_keyboard(track, is_favorite=is_favorite)

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


def handle_track_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Handles selected track button.
    """
    try:
        bot.answer_callback_query(call.id)

        track = get_track(track_id)
        save_track(track)

        send_track_card(
            bot=bot,
            chat_id=call.message.chat.id,
            telegram_id=call.from_user.id,
            track=track,
        )

    except Exception as error:
        logger.exception("Track callback error: %s", error)
        bot.send_message(
            call.message.chat.id,
            "Could not load track information.",
        )


def handle_page_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    page: int,
) -> None:
    """
    Changes current search results page without calling Deezer API again.
    """
    try:
        context = get_search_context(call.from_user.id)

        if not context:
            bot.answer_callback_query(
                call.id,
                "Search session expired. Please search again.",
                show_alert=True,
            )
            return

        normalized_page = set_search_page(
            user_id=call.from_user.id,
            page=page,
            page_size=settings.RESULTS_PER_PAGE,
        )

        total_pages = get_total_pages(
            user_id=call.from_user.id,
            page_size=settings.RESULTS_PER_PAGE,
        )
        page_tracks = get_page_tracks(
            user_id=call.from_user.id,
            page_size=settings.RESULTS_PER_PAGE,
            page=normalized_page,
        )

        markup = search_results_keyboard(
            tracks=page_tracks,
            page=normalized_page,
            total_pages=total_pages,
        )

        query = context.get("query", "")
        total_tracks = len(context.get("tracks", []))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Found {total_tracks} tracks for: {query}",
            reply_markup=markup,
        )

        bot.answer_callback_query(call.id)

    except Exception as error:
        logger.exception("Pagination callback error: %s", error)
        bot.answer_callback_query(
            call.id,
            "Could not change page.",
            show_alert=True,
        )


def handle_history_search_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    search_id: str,
) -> None:
    """
    Repeats selected search query from history.
    """
    try:
        query = get_search_query_by_id(
            telegram_id=call.from_user.id,
            search_id=int(search_id),
        )

        if not query:
            bot.answer_callback_query(
                call.id,
                "History item was not found.",
                show_alert=True,
            )
            return

        bot.answer_callback_query(call.id, "Searching again...")

        upsert_user(call.from_user)

        send_search_results(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            query=query,
            save_to_history=True,
        )

    except Exception as error:
        logger.exception("History search callback error: %s", error)
        bot.send_message(
            call.message.chat.id,
            "Could not repeat this search.",
        )


def handle_clear_history_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Clears current user's search history.
    """
    try:
        clear_search_history(call.from_user.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=HISTORY_EMPTY_TEXT,
        )

        bot.answer_callback_query(
            call.id,
            "History cleared.",
            show_alert=False,
        )

    except Exception as error:
        logger.exception("Clear history callback error: %s", error)
        bot.answer_callback_query(
            call.id,
            "Could not clear history.",
            show_alert=True,
        )


def handle_favorite_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Adds track to favorites and updates inline button.
    """
    try:
        upsert_user(call.from_user)

        track = get_track(track_id)
        save_track(track)
        add_favorite(call.from_user.id, track)

        updated_markup = track_actions_keyboard(
            track,
            is_favorite=True,
        )

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=updated_markup,
        )

        bot.answer_callback_query(
            call.id,
            FAVORITE_ADDED_TEXT,
            show_alert=False,
        )

    except Exception as error:
        logger.exception("Favorite callback error: %s", error)
        bot.answer_callback_query(
            call.id,
            "Could not add to favorites.",
            show_alert=True,
        )


def handle_remove_favorite_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Removes track from favorites and updates inline button.
    """
    try:
        track = get_track(track_id)
        save_track(track)

        remove_favorite(
            telegram_id=call.from_user.id,
            deezer_track_id=track_id,
        )

        updated_markup = track_actions_keyboard(
            track,
            is_favorite=False,
        )

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=updated_markup,
        )

        bot.answer_callback_query(
            call.id,
            FAVORITE_REMOVED_TEXT,
            show_alert=False,
        )

    except Exception as error:
        logger.exception("Remove favorite callback error: %s", error)
        bot.answer_callback_query(
            call.id,
            "Could not remove from favorites.",
            show_alert=True,
        )


def handle_lyrics_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Finds Genius lyrics page for selected track.
    """
    try:
        bot.answer_callback_query(call.id, "Searching lyrics...")

        track = get_track(track_id)

        lyrics_url = find_lyrics_url(
            title=track["title"],
            artist=track["artist"],
        )

        if not lyrics_url:
            bot.send_message(call.message.chat.id, LYRICS_NOT_FOUND_TEXT)
            return

        bot.send_message(
            call.message.chat.id,
            "Lyrics page found:",
            reply_markup=genius_url_keyboard(lyrics_url),
        )

    except Exception as error:
        logger.exception("Lyrics callback error: %s", error)
        bot.send_message(call.message.chat.id, GENIUS_ERROR_TEXT)


def register_callbacks(bot: telebot.TeleBot) -> None:
    """
    Registers all callback query handlers.
    """

    @bot.callback_query_handler(func=lambda call: True)
    def callback_router(call: types.CallbackQuery) -> None:
        data = call.data or ""

        if data == "noop":
            bot.answer_callback_query(call.id)
            return

        if data.startswith("page:"):
            page = int(data.split(":", 1)[1])
            handle_page_callback(bot, call, page)
            return

        if data.startswith("hist:"):
            search_id = data.split(":", 1)[1]
            handle_history_search_callback(bot, call, search_id)
            return

        if data == "history_clear":
            handle_clear_history_callback(bot, call)
            return

        if data.startswith("track:"):
            track_id = data.split(":", 1)[1]
            handle_track_callback(bot, call, track_id)
            return

        if data.startswith("fav:"):
            track_id = data.split(":", 1)[1]
            handle_favorite_callback(bot, call, track_id)
            return

        if data.startswith("unfav:"):
            track_id = data.split(":", 1)[1]
            handle_remove_favorite_callback(bot, call, track_id)
            return

        if data.startswith("lyrics:"):
            track_id = data.split(":", 1)[1]
            handle_lyrics_callback(bot, call, track_id)
            return

        if data == "search_again":
            bot.answer_callback_query(call.id)
            ask_for_music(bot, call.message.chat.id)
            return

        bot.answer_callback_query(
            call.id,
            "Unknown action.",
            show_alert=False,
        )
