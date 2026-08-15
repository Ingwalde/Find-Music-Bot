import asyncio

from aiogram import Bot
from aiogram.types import LinkPreviewOptions

from app.bot.context import (
    get_current_page,
    get_page_tracks,
    get_search_context,
    get_total_pages,
    save_search_context,
)
from app.bot.keyboards import (
    main_menu_keyboard,
    search_mode_keyboard,
    search_results_keyboard,
    track_actions_keyboard,
)
from app.config.admins import is_admin_user
from app.config.settings import settings
from app.database.repositories import (
    get_user_language,
    is_track_favorite,
    save_last_track_id,
    save_search,
)
from app.localization.translations import t
from app.services.recommendations_service import format_recommendations_text, get_db_recommendations
from app.services.search_cache_service import search_tracks_cached
from app.services.track_formatter import format_track_card
from app.services.track_platform_service import enrich_track_with_spotify_link
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.utils.text import split_long_message
from app.utils.types import TrackDict

logger = setup_logger(__name__)


async def send_long_message(bot: Bot, chat_id: int, text: str) -> None:
    """
    Sends text that may exceed Telegram's 4096-character message limit.

    split_long_message() existed and was tested from the day it was written,
    but was never called from production code — so any report long enough to
    need it hit the API limit instead. The admin reports are the realistic
    case: /errors renders up to ERROR_HISTORY_LIMIT entries whose text comes
    from arbitrary exception messages, with nothing bounding the total.
    """
    for chunk in split_long_message(text):
        await bot.send_message(chat_id, chunk)


async def user_has_search_context(user_id: int) -> bool:
    context = await get_search_context(user_id)
    return bool(context and context.get("tracks"))


async def show_main_menu(
    bot: Bot,
    chat_id: int,
    user_id: int | None = None,
) -> None:
    if user_id:
        language = await get_user_language(user_id)
        is_admin = await asyncio.to_thread(is_admin_user, user_id)
    else:
        language = "en"
        is_admin = False

    await bot.send_message(
        chat_id,
        t("main_menu", language),
        reply_markup=main_menu_keyboard(language, is_admin=is_admin),
    )


async def ask_for_music(
    bot: Bot,
    chat_id: int,
    user_id: int | None = None,
) -> None:
    language = await get_user_language(user_id) if user_id else "en"

    await bot.send_message(
        chat_id,
        t("ask_music", language),
        reply_markup=search_mode_keyboard(language),
    )


async def send_search_results(
    bot: Bot,
    chat_id: int,
    user_id: int,
    query: str,
    save_to_history: bool = True,
) -> None:
    language = await get_user_language(user_id)
    query = query.strip()

    if not query:
        await bot.send_message(chat_id, t("search_query_empty", language))
        await ask_for_music(bot, chat_id, user_id)
        return

    if save_to_history:
        await save_search(user_id, query)

    tracks = await search_tracks_cached(
        query=query,
        limit=settings.MAX_SEARCH_RESULTS,
    )

    if not tracks:
        await bot.send_message(chat_id, t("no_results", language))
        await ask_for_music(bot, chat_id, user_id)
        return

    await save_search_context(user_id=user_id, query=query, tracks=tracks)

    total_pages = await get_total_pages(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
    )

    page_tracks = await get_page_tracks(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
        page=0,
    )

    markup = search_results_keyboard(
        tracks=page_tracks,
        page=0,
        total_pages=total_pages,
    )

    await bot.send_message(
        chat_id,
        t("search_found", language, count=len(tracks), query=query),
        reply_markup=markup,
    )


async def send_current_results_page(
    bot: Bot,
    chat_id: int,
    user_id: int,
) -> None:
    language = await get_user_language(user_id)
    context = await get_search_context(user_id)

    if not context:
        await bot.send_message(chat_id, t("back_to_results_empty", language))
        return

    page = await get_current_page(user_id)

    total_pages = await get_total_pages(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
    )

    page_tracks = await get_page_tracks(
        user_id=user_id,
        page_size=settings.RESULTS_PER_PAGE,
        page=page,
    )

    if not page_tracks:
        await bot.send_message(chat_id, t("back_to_results_empty", language))
        return

    markup = search_results_keyboard(
        tracks=page_tracks,
        page=page,
        total_pages=total_pages,
    )

    query = context.get("query", "")
    total_tracks = len(context.get("tracks", []))

    await bot.send_message(
        chat_id,
        t("search_found", language, count=total_tracks, query=query),
        reply_markup=markup,
    )


async def send_track_card(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    track: TrackDict,
) -> None:
    language = await get_user_language(telegram_id)

    track = await enrich_track_with_spotify_link(track)

    deezer_id = track.get("deezer_track_id")
    if deezer_id:
        try:
            await save_last_track_id(telegram_id, deezer_id)
        except Exception as error:
            await log_and_save_error(logger, telegram_id, "send_track_card_last_track_id", error)

    text = format_track_card(track)

    is_favorite = await is_track_favorite(
        telegram_id=telegram_id,
        deezer_track_id=track["deezer_track_id"],
    )

    markup = track_actions_keyboard(
        track,
        is_favorite=is_favorite,
        show_back_to_results=await user_has_search_context(telegram_id),
        language=language,
    )

    cover_url = track.get("cover_url")

    if cover_url:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=cover_url,
                caption=text,
                reply_markup=markup,
            )
        except Exception as error:
            await log_and_save_error(logger, telegram_id, "send_track_card_cover_image", error)
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
        )

    try:
        artist = track.get("artist", "")
        exclude_id = track.get("deezer_track_id", "")
        if artist and exclude_id:
            recs = await get_db_recommendations(artist=artist, exclude_deezer_id=exclude_id)
            if recs:
                rec_text = format_recommendations_text(recs, source_artist=artist)
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"{t('you_may_also_like', language)}\n\n{rec_text}",
                    parse_mode="Markdown",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
    except Exception as error:
        await log_and_save_error(logger, telegram_id, "send_track_card_recommendations", error)
