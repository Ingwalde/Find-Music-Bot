import telebot
from telebot import types

from app.bot.context import (
    get_page_tracks,
    get_search_context,
    get_total_pages,
    set_search_page,
)
from app.bot.keyboards import search_results_keyboard
from app.config.settings import settings
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


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
        log_and_save_error(logger, call.from_user.id, "pagination_callback", error)
        bot.answer_callback_query(
            call.id,
            "Could not change page.",
            show_alert=True,
        )


def handle_back_to_results_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
) -> None:
    """
    Returns user to current saved search results page.
    """
    from app.bot.actions import send_current_results_page

    try:
        bot.answer_callback_query(call.id)

        send_current_results_page(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
        )

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "back_to_results_callback", error)
        bot.answer_callback_query(
            call.id,
            "Could not return to results.",
            show_alert=True,
        )
