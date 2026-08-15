from aiogram import Bot
from aiogram.types import CallbackQuery, LinkPreviewOptions

from app.bot.rate_limit import check_rate_limit, should_warn_once
from app.database.repositories import get_user_language
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.services.recommendations_service import format_similar_text, get_similar_by_genre
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_similar_callback(
    bot: Bot,
    call: CallbackQuery,
    track_id: str,
) -> None:
    """
    Handles the 🎯 Similar button — fetches and displays tracks similar to
    the selected track using the Deezer radio endpoint.
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

    await bot.answer_callback_query(call.id)

    source_track = None
    try:
        try:
            source_track = await get_track(track_id)
            header = t(
                "similar_header",
                language,
                title=source_track.get("title", ""),
                artist=source_track.get("artist", ""),
            )
        except Exception:
            header = t("similar_header", language, title="", artist="").rstrip(" —").rstrip()

        artist_name = source_track.get("artist", "") if source_track else ""
        tracks = await get_similar_by_genre(track_id, artist_name=artist_name)

        if not tracks:
            await bot.send_message(message.chat.id, t("similar_empty", language))
            return

        text = format_similar_text(header, tracks[:5], artist_name)
        await bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="similar_callback",
            error=error,
        )
        await bot.send_message(message.chat.id, t("similar_empty", language))
