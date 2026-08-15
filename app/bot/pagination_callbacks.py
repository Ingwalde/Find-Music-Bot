from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.context import (
    get_page_tracks,
    get_search_context,
    get_total_pages,
    set_search_page,
)
from app.bot.keyboards import search_results_keyboard
from app.config.settings import settings
from app.database.repositories import get_user_language
from app.localization.translations import t
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_page_callback(
    bot: Bot,
    call: CallbackQuery,
    page: int,
) -> None:
    # Narrowed once. The router rejects any callback whose message or
    # from_user is absent, so neither can be None here — binding them
    # keeps that in the type system instead of re-asserting per use.
    message = call.message
    user = call.from_user
    if message is None or user is None:
        return

    language = await get_user_language(user.id)

    try:
        context = await get_search_context(user.id)

        if not context:
            await bot.answer_callback_query(
                call.id,
                t("search_session_expired", language),
                show_alert=True,
            )
            return

        normalized_page = await set_search_page(
            user_id=user.id,
            page=page,
            page_size=settings.RESULTS_PER_PAGE,
        )

        total_pages = await get_total_pages(
            user_id=user.id,
            page_size=settings.RESULTS_PER_PAGE,
        )

        page_tracks = await get_page_tracks(
            user_id=user.id,
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

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=t("search_found", language, count=total_tracks, query=query),
            reply_markup=markup,
        )

        await bot.answer_callback_query(call.id)

    except Exception as error:
        await log_and_save_error(logger, user.id, "pagination_callback", error)
        await bot.answer_callback_query(
            call.id, t("could_not_change_page", language), show_alert=True
        )


async def handle_back_to_results_callback(
    bot: Bot,
    call: CallbackQuery,
) -> None:
    # Narrowed once. The router rejects any callback whose message or
    # from_user is absent, so neither can be None here — binding them
    # keeps that in the type system instead of re-asserting per use.
    message = call.message
    user = call.from_user
    if message is None or user is None:
        return

    from app.bot.actions import send_current_results_page

    language = await get_user_language(user.id)

    try:
        await bot.answer_callback_query(call.id)

        await send_current_results_page(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user.id,
        )

    except Exception as error:
        await log_and_save_error(logger, user.id, "back_to_results_callback", error)
        await bot.answer_callback_query(
            call.id, t("could_not_return_results", language), show_alert=True
        )
