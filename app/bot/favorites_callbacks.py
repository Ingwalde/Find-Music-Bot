import telebot
from telebot import types

from app.bot.actions import user_has_search_context
from app.bot.keyboards import (
    confirm_clear_favorites_keyboard,
    favorites_keyboard,
    track_actions_keyboard,
)
from app.bot.messages import (
    FAVORITE_ADDED_TEXT,
    FAVORITE_REMOVED_TEXT,
    FAVORITES_CLEAR_CONFIRM_TEXT,
    FAVORITES_CLEARED_TEXT,
    FAVORITES_EMPTY_TEXT,
)
from app.database.repositories import (
    add_favorite,
    clear_favorites,
    get_favorite_tracks,
    remove_favorite,
    save_track,
    upsert_user,
)
from app.services.deezer_service import get_track
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


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
            show_back_to_results=user_has_search_context(call.from_user.id),
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
        log_and_save_error(logger, call.from_user.id, "favorite_callback", error)
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
            show_back_to_results=user_has_search_context(call.from_user.id),
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
        log_and_save_error(logger, call.from_user.id, "remove_favorite_callback", error)
        bot.answer_callback_query(
            call.id,
            "Could not remove from favorites.",
            show_alert=True,
        )


def handle_clear_favorites_request_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Asks user to confirm favorites clearing.
    """
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=FAVORITES_CLEAR_CONFIRM_TEXT,
            reply_markup=confirm_clear_favorites_keyboard(),
        )
        bot.answer_callback_query(call.id)
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_favorites_request", error)
        bot.answer_callback_query(call.id, "Could not open confirmation.", show_alert=True)


def handle_clear_favorites_confirm_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Clears all user favorites after confirmation.
    """
    try:
        clear_favorites(call.from_user.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=FAVORITES_CLEARED_TEXT,
        )
        bot.answer_callback_query(call.id, "Favorites cleared.")
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_favorites_confirm", error)
        bot.answer_callback_query(call.id, "Could not clear favorites.", show_alert=True)


def handle_clear_favorites_cancel_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Cancels favorites clearing and returns to favorites list.
    """
    try:
        tracks = get_favorite_tracks(call.from_user.id)

        if not tracks:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=FAVORITES_EMPTY_TEXT,
            )
            bot.answer_callback_query(call.id)
            return

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⭐ Your favorite tracks: {len(tracks)}\n\nClick a track to open its card:",
            reply_markup=favorites_keyboard(tracks),
        )
        bot.answer_callback_query(call.id, "Cancelled.")
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_favorites_cancel", error)
        bot.answer_callback_query(call.id, "Could not cancel.", show_alert=True)
