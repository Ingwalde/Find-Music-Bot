from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.actions import send_track_card
from app.bot.rate_limit import check_rate_limit, should_warn_once
from app.database.repositories import get_track_by_deezer_id, get_user_language, save_track
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.utils.types import TrackDict

logger = setup_logger(__name__)


async def get_track_from_cache_or_deezer(track_id: str) -> TrackDict:
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
        await bot.answer_callback_query(call.id)

        track = await get_track_from_cache_or_deezer(track_id)

        await send_track_card(
            bot=bot,
            chat_id=message.chat.id,
            telegram_id=user.id,
            track=track,
        )

    except Exception as error:
        await log_and_save_error(logger, user.id, "track_callback", error)
        await bot.send_message(message.chat.id, t("could_not_load_track", language))
