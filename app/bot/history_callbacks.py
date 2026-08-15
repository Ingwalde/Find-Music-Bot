from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.actions import send_search_results
from app.bot.keyboards import confirm_clear_history_keyboard, history_keyboard
from app.bot.rate_limit import check_rate_limit, should_warn_once
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


async def handle_history_search_callback(
    bot: Bot,
    call: CallbackQuery,
    search_id: str,
) -> None:
    # Narrowed once. The router rejects any callback whose message or
    # from_user is absent, so neither can be None here — binding them
    # keeps that in the type system instead of re-asserting per use.
    message = call.message
    user = call.from_user
    if message is None or user is None:
        return

    language = await get_user_language(user.id)

    if not await check_rate_limit(user.id):
        if await should_warn_once(user.id):
            await bot.answer_callback_query(call.id, t("rate_limit_exceeded", language), show_alert=True)
        else:
            await bot.answer_callback_query(call.id)
        return

    try:
        query = await get_search_query_by_id(
            telegram_id=user.id,
            search_id=int(search_id),
        )

        if not query:
            await bot.answer_callback_query(
                call.id, t("history_item_not_found", language), show_alert=True
            )
            return

        await bot.answer_callback_query(call.id, t("searching_again", language))
        await upsert_user(user)

        await send_search_results(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user.id,
            query=query,
            save_to_history=True,
        )

    except Exception as error:
        await log_and_save_error(logger, user.id, "history_search_callback", error)
        await bot.send_message(message.chat.id, t("could_not_repeat_search", language))


async def handle_clear_history_request_callback(
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

    language = await get_user_language(user.id)

    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=t("history_clear_confirm", language),
            reply_markup=confirm_clear_history_keyboard(language),
        )
        await bot.answer_callback_query(call.id)
    except Exception as error:
        await log_and_save_error(logger, user.id, "clear_history_request", error)
        await bot.answer_callback_query(
            call.id, t("could_not_open_confirmation", language), show_alert=True
        )


async def handle_clear_history_confirm_callback(
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

    language = await get_user_language(user.id)

    try:
        await clear_search_history(user.id)

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=t("history_cleared", language),
        )

        await bot.answer_callback_query(
            call.id, t("history_cleared", language), show_alert=False
        )

    except Exception as error:
        await log_and_save_error(logger, user.id, "clear_history_callback", error)
        await bot.answer_callback_query(
            call.id, t("could_not_clear_history", language), show_alert=True
        )


async def handle_clear_history_cancel_callback(
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

    language = await get_user_language(user.id)

    try:
        history = await get_search_history(
            user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=t("history_empty", language),
            )
            await bot.answer_callback_query(call.id)
            return

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=t("history_title", language, count=len(history)),
            reply_markup=history_keyboard(history, language),
        )

        await bot.answer_callback_query(call.id, t("cancelled", language))

    except Exception as error:
        await log_and_save_error(logger, user.id, "clear_history_cancel", error)
        await bot.answer_callback_query(
            call.id, t("could_not_cancel", language), show_alert=True
        )
