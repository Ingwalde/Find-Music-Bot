from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.keyboards import genius_url_keyboard
from app.bot.rate_limit import check_rate_limit, should_warn_once
from app.database.repositories import get_user_language
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.services.lyrics_service import find_lyrics_url
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_lyrics_callback(
    bot: Bot,
    call: CallbackQuery,
    track_id: str,
) -> None:
    """
    Finds Genius lyrics page for selected track.
    """
    language = await get_user_language(call.from_user.id)

    if not await check_rate_limit(call.from_user.id):
        if await should_warn_once(call.from_user.id):
            await bot.answer_callback_query(call.id, t("rate_limit_exceeded", language), show_alert=True)
        else:
            await bot.answer_callback_query(call.id)
        return

    await bot.answer_callback_query(call.id)

    try:
        track = await get_track(track_id)
        lyrics_url = await find_lyrics_url(
            title=track["title"],
            artist=track["artist"],
        )
    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "lyrics_callback", error)
        await bot.send_message(call.message.chat.id, t("genius_error", language))
        return

    if not lyrics_url:
        await bot.send_message(call.message.chat.id, t("lyrics_not_found", language))
        return

    await bot.send_message(
        call.message.chat.id,
        t("lyrics_page_found", language),
        reply_markup=genius_url_keyboard(lyrics_url, language),
    )
