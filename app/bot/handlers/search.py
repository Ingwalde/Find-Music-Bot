from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import LinkPreviewOptions, Message

from app.bot.actions import ask_for_music, send_search_results
from app.bot.handlers._shared import get_user_context, is_admin
from app.bot.rate_limit import check_rate_limit, should_warn_once
from app.localization.translations import t
from app.services.deezer_service import get_track as deezer_get_track
from app.services.deezer_service import get_trending_tracks
from app.services.recommendations_service import (
    format_recommendations_text,
    format_similar_text,
    get_cached_trending,
    get_similar_by_genre,
)
from app.services.user_service import get_last_track_id
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = Router(name="handlers.search")


async def process_music_search(bot: Bot, message: Message) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)

    if not message.text:
        await bot.send_message(message.chat.id, t("please_send_text", language))
        await ask_for_music(bot, message.chat.id, user.id)
        return

    text = message.text.strip()

    if text.startswith("/"):
        return

    user_is_admin = await is_admin(user.id)
    if not await check_rate_limit(user.id, is_admin=user_is_admin):
        if await should_warn_once(user.id):
            await bot.send_message(message.chat.id, t("rate_limit_exceeded", language))
        return

    try:
        await send_search_results(
            bot=bot,
            chat_id=message.chat.id,
            user_id=user.id,
            query=text,
            save_to_history=True,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="music_search",
            error=error,
        )
        await bot.send_message(message.chat.id, t("something_wrong_searching", language))


@router.message(Command("similar"))
async def similar_handler(message: Message, bot: Bot) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)

    last_track_id = await get_last_track_id(user.id)

    if not last_track_id:
        await bot.send_message(message.chat.id, t("similar_no_context", language))
        return

    user_is_admin = await is_admin(user.id)
    if not await check_rate_limit(user.id, is_admin=user_is_admin):
        if await should_warn_once(user.id):
            await bot.send_message(message.chat.id, t("rate_limit_exceeded", language))
        return

    source = None
    try:
        try:
            source = await deezer_get_track(last_track_id)
            header = t(
                "similar_header",
                language,
                title=source.get("title", ""),
                artist=source.get("artist", ""),
            )
        except Exception:
            header = t("similar_header", language, title="", artist="").rstrip(" —").rstrip()

        artist_name = source.get("artist", "") if source else ""
        tracks = await get_similar_by_genre(last_track_id, artist_name=artist_name)

        if not tracks:
            await bot.send_message(message.chat.id, t("similar_empty", language))
            return

        text = format_similar_text(header, tracks[:5], artist_name)
        # original /similar had no link_preview — behavior preserved
        await bot.send_message(message.chat.id, text, parse_mode="Markdown")

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="similar_handler",
            error=error,
        )
        await bot.send_message(message.chat.id, t("similar_empty", language))


@router.message(Command("trending"))
async def trending_handler(message: Message, bot: Bot) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)

    user_is_admin = await is_admin(user.id)
    if not await check_rate_limit(user.id, is_admin=user_is_admin):
        if await should_warn_once(user.id):
            await bot.send_message(message.chat.id, t("rate_limit_exceeded", language))
        return

    try:
        tracks = await get_cached_trending(get_trending_tracks)

        if not tracks:
            await bot.send_message(message.chat.id, t("trending_empty", language))
            return

        text_lines = [t("trending_header", language), format_recommendations_text(tracks[:10])]

        await bot.send_message(
            message.chat.id,
            "\n".join(text_lines),
            parse_mode="Markdown",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="trending_handler",
            error=error,
        )
        await bot.send_message(message.chat.id, t("trending_empty", language))
