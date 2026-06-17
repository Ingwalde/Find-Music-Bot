from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.actions import send_track_card
from app.database.repositories import get_track_by_deezer_id, get_user_language, save_track
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def get_track_from_cache_or_deezer(track_id: str) -> dict:
    """
    Loads track from the database cache first.
    Falls back to Deezer API only if the track is not cached yet.
    """
    cached_track = await get_track_by_deezer_id(track_id)

    if cached_track:
        logger.info("Track %s loaded from DB cache.", track_id)
        return cached_track

    logger.info("Track %s was not cached. Loading from Deezer.", track_id)

    track = await get_track(track_id)
    await save_track(track)

    return track


async def handle_track_callback(
    bot: Bot,
    call: CallbackQuery,
    track_id: str,
) -> None:
    """
    Handles selected track button.
    Uses cached track metadata when possible.
    """
    language = await get_user_language(call.from_user.id)

    try:
        await bot.answer_callback_query(call.id)

        track = await get_track_from_cache_or_deezer(track_id)

        await send_track_card(
            bot=bot,
            chat_id=call.message.chat.id,
            telegram_id=call.from_user.id,
            track=track,
        )

    except Exception as error:
        await log_and_save_error(logger, call.from_user.id, "track_callback", error)
        await bot.send_message(call.message.chat.id, t("could_not_load_track", language))
