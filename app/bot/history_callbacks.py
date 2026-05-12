import telebot
from telebot import types

from app.bot.actions import send_search_results
from app.bot.keyboards import confirm_clear_history_keyboard, history_keyboard
from app.config.settings import settings
from app.database.repositories import (
    clear_search_history,
    get_search_history,
    get_search_query_by_id,
    get_user_language,
    upsert_user,
)
from app.localization.translations import t
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
    language = get_user_language(call.from_user.id)

    try:
        query = get_search_query_by_id(
            telegram_id=call.from_user.id,
            search_id=int(search_id),
        )

        if not query:
            bot.answer_callback_query(call.id, t("history_item_not_found", language), show_alert=True)
            return

        bot.answer_callback_query(call.id, t("searching_again", language))
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
        bot.send_message(call.message.chat.id, t("could_not_repeat_search", language))


def handle_clear_history_request_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Asks user to confirm history clearing.
    """
    language = get_user_language(call.from_user.id)

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("history_clear_confirm", language),
            reply_markup=confirm_clear_history_keyboard(language),
        )
        bot.answer_callback_query(call.id)
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_request", error)
        bot.answer_callback_query(call.id, t("could_not_open_confirmation", language), show_alert=True)


def handle_clear_history_confirm_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Clears current user's search history after confirmation.
    """
    language = get_user_language(call.from_user.id)

    try:
        clear_search_history(call.from_user.id)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("history_cleared", language),
        )

        bot.answer_callback_query(call.id, t("history_cleared", language), show_alert=False)

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_callback", error)
        bot.answer_callback_query(call.id, t("could_not_clear_history", language), show_alert=True)


def handle_clear_history_cancel_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Cancels history clearing and returns to history list.
    """
    language = get_user_language(call.from_user.id)

    try:
        history = get_search_history(
            call.from_user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=t("history_empty", language),
            )
            bot.answer_callback_query(call.id)
            return

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("history_title", language, count=len(history)),
            reply_markup=history_keyboard(history, language),
        )

        bot.answer_callback_query(call.id, t("cancelled", language))

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "clear_history_cancel", error)
        bot.answer_callback_query(call.id, t("could_not_cancel", language), show_alert=True)
