from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.actions import user_has_search_context
from app.bot.keyboards import (
    confirm_clear_favorites_keyboard,
    favorites_keyboard,
    track_actions_keyboard,
)
from app.bot.rate_limit import check_rate_limit, should_warn_once
from app.database.repositories import (
    add_favorite,
    clear_favorites,
    get_favorite_tracks,
    get_user_language,
    remove_favorite,
    save_track,
    upsert_user,
)
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_favorite_callback(
    bot: Bot,
    call: CallbackQuery,
    track_id: str,
) -> None:
    language = await get_user_language(call.from_user.id)

    if not await check_rate_limit(call.from_user.id):
        if await should_warn_once(call.from_user.id):
            await bot.answer_callback_query(call.id, t("rate_limit_exceeded", language), show_alert=True)
        else:
            await bot.answer_callback_query(call.id)
        return

    try:
        await upsert_user(call.from_user)

        track = await get_track(track_id)
        await save_track(track)
        await add_favorite(call.from_user.id, track)

        updated_markup = track_actions_keyboard(
            track,
            is_favorite=True,
            show_back_to_results=await user_has_search_context(call.from_user.id),
            language=language,
        )

        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=updated_markup,
        )

        await bot.answer_callback_query(call.id, t("favorite_added", language), show_alert=False)

    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "favorite_callback", error)
        await bot.answer_callback_query(call.id, t("favorite_add_failed", language), show_alert=True)


async def handle_remove_favorite_callback(
    bot: Bot,
    call: CallbackQuery,
    track_id: str,
) -> None:
    language = await get_user_language(call.from_user.id)

    if not await check_rate_limit(call.from_user.id):
        if await should_warn_once(call.from_user.id):
            await bot.answer_callback_query(call.id, t("rate_limit_exceeded", language), show_alert=True)
        else:
            await bot.answer_callback_query(call.id)
        return

    try:
        track = await get_track(track_id)
        await save_track(track)

        await remove_favorite(
            telegram_id=call.from_user.id,
            deezer_track_id=track_id,
        )

        updated_markup = track_actions_keyboard(
            track,
            is_favorite=False,
            show_back_to_results=await user_has_search_context(call.from_user.id),
            language=language,
        )

        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=updated_markup,
        )

        await bot.answer_callback_query(call.id, t("favorite_removed", language), show_alert=False)

    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "remove_favorite_callback", error)
        await bot.answer_callback_query(
            call.id, t("favorite_remove_failed", language), show_alert=True
        )


async def handle_clear_favorites_request_callback(
    bot: Bot,
    call: CallbackQuery,
) -> None:
    language = await get_user_language(call.from_user.id)

    try:
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("favorites_clear_confirm", language),
            reply_markup=confirm_clear_favorites_keyboard(language),
        )
        await bot.answer_callback_query(call.id)
    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "clear_favorites_request", error)
        await bot.answer_callback_query(
            call.id, t("could_not_open_confirmation", language), show_alert=True
        )


async def handle_clear_favorites_confirm_callback(
    bot: Bot,
    call: CallbackQuery,
) -> None:
    language = await get_user_language(call.from_user.id)

    try:
        await clear_favorites(call.from_user.id)

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("favorites_cleared", language),
        )
        await bot.answer_callback_query(call.id, t("favorites_cleared", language))
    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "clear_favorites_confirm", error)
        await bot.answer_callback_query(
            call.id, t("could_not_clear_favorites", language), show_alert=True
        )


async def handle_clear_favorites_cancel_callback(
    bot: Bot,
    call: CallbackQuery,
) -> None:
    language = await get_user_language(call.from_user.id)

    try:
        tracks = await get_favorite_tracks(call.from_user.id)

        if not tracks:
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=t("favorites_empty", language),
            )
            await bot.answer_callback_query(call.id)
            return

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=t("favorites_title", language, count=len(tracks)),
            reply_markup=favorites_keyboard(tracks, language),
        )
        await bot.answer_callback_query(call.id, t("cancelled", language))
    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "clear_favorites_cancel", error)
        await bot.answer_callback_query(
            call.id, t("could_not_cancel", language), show_alert=True
        )
