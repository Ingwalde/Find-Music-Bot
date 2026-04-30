import telebot
from telebot import types

from app.bot.actions import send_search_results
from app.bot.keyboards import confirm_clear_history_keyboard, history_keyboard
from app.bot.messages import (
    HISTORY_CLEAR_CONFIRM_TEXT,
    HISTORY_CLEARED_TEXT,
    HISTORY_EMPTY_TEXT,
)
from app.config.settings import settings
from app.database.repositories import (
    clear_search_history,
    get_search_history,
    get_search_query_by_id,
    upsert_user,
)
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


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
        log_and_save_error(logger, call.from_user.id, "history_search_callback", error)
        bot.send_message(
            call.message.chat.id,
            "Could not repeat this search.",
        )


def handle_clear_history_request_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Asks user to confirm history clearing.
    """
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=HISTORY_CLEAR_CONFIRM_TEXT,
            reply_markup=confirm_clear_history_keyboard(),
        )
        bot.answer_callback_query(call.id)
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_request", error)
        bot.answer_callback_query(call.id, "Could not open confirmation.", show_alert=True)


def handle_clear_history_confirm_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Clears current user's search history after confirmation.
    """
    try:
        clear_search_history(call.from_user.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=HISTORY_CLEARED_TEXT,
        )

        bot.answer_callback_query(
            call.id,
            "History cleared.",
            show_alert=False,
        )

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_callback", error)
        bot.answer_callback_query(
            call.id,
            "Could not clear history.",
            show_alert=True,
        )


def handle_clear_history_cancel_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Cancels history clearing and returns to history list.
    """
    try:
        history = get_search_history(
            call.from_user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=HISTORY_EMPTY_TEXT,
            )
            bot.answer_callback_query(call.id)
            return

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🕘 Your recent searches: {len(history)}\n\nClick a query to search again:",
            reply_markup=history_keyboard(history),
        )

        bot.answer_callback_query(call.id, "Cancelled.")

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_cancel", error)
        bot.answer_callback_query(call.id, "Could not cancel.", show_alert=True)
