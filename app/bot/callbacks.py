import telebot
from telebot import types

from app.bot.handlers import ask_for_music
from app.bot.keyboards import (
    track_actions_keyboard,
    genius_url_keyboard,
)
from app.bot.messages import (
    FAVORITE_ADDED_TEXT,
    FAVORITE_REMOVED_TEXT,
    LYRICS_NOT_FOUND_TEXT,
    GENIUS_ERROR_TEXT,
)
from app.database.repositories import (
    upsert_user,
    save_track,
    add_favorite,
    remove_favorite,
    is_track_favorite,
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
            ask_for_music(
                bot=bot,
                chat_id=call.message.chat.id,
                user_id=call.from_user.id
            )
            return

        bot.answer_callback_query(
            call.id,
            "Unknown action.",
            show_alert=False,
        )
