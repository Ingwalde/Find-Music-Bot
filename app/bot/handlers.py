import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import LinkPreviewOptions, Message

from app.admin_tools import (
    cleanup_errors_report,
    cleanup_history_report,
    format_maintenance_report,
    format_stats_report,
    reload_admins_report,
)
from app.bot.actions import (
    ask_for_music,
    send_search_results,
    show_main_menu,
)
from app.bot.keyboards import (
    admin_menu_keyboard,
    favorites_keyboard,
    history_keyboard,
    language_keyboard,
    main_menu_keyboard,
    search_mode_keyboard,
)
from app.config.admins import is_admin_user
from app.config.settings import settings
from app.database.repositories import (
    clear_errors,
    get_favorite_tracks,
    get_last_track_id,
    get_recent_errors,
    get_search_history,
    get_user_language,
    upsert_user,
)
from app.health import format_health_report
from app.localization.translations import get_menu_action_by_text, t
from app.services.deezer_service import get_track as deezer_get_track
from app.services.deezer_service import get_trending_tracks
from app.services.recommendations_service import (
    format_recommendations_text,
    format_similar_text,
    get_cached_trending,
    get_similar_by_genre,
)
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.version import __version__

logger = setup_logger(__name__)

router = Router(name="handlers")


# ── helpers ──────────────────────────────────────────────────────────────────


async def is_admin(user_id: int | None) -> bool:
    return await asyncio.to_thread(is_admin_user, user_id)


async def get_user_context(message: Message) -> str:
    await upsert_user(message.from_user)
    return await get_user_language(message.from_user.id)


async def require_admin(bot: Bot, message: Message, language: str) -> bool:
    if not await is_admin(message.from_user.id):
        await bot.send_message(message.chat.id, t("admin_only", language))
        return False
    return True


async def format_recent_errors(language: str = "en") -> str:
    errors = await get_recent_errors(limit=settings.ERROR_HISTORY_LIMIT)

    if not errors:
        return t("errors_empty", language)

    lines = [t("errors_header", language)]

    for index, item in enumerate(errors, start=1):
        source = item.get("source", "unknown")
        created_at = item.get("created_at", "unknown time")
        error_message = item.get("error_message", "Unknown error")
        telegram_id = item.get("telegram_id")

        user_part = f" | user: {telegram_id}" if telegram_id else ""
        lines.append(
            f"{index}. [{created_at}] {source}{user_part}\n"
            f"   {error_message}"
        )

    return "\n".join(lines)


async def send_admin_only_message(bot: Bot, message: Message, language: str) -> None:
    await bot.send_message(message.chat.id, t("admin_only", language))


async def show_admin_menu(bot: Bot, message: Message) -> None:
    language = await get_user_context(message)

    if not await is_admin(message.from_user.id):
        await send_admin_only_message(bot, message, language)
        return

    await bot.send_message(
        message.chat.id,
        t("admin_menu", language),
        reply_markup=admin_menu_keyboard(language),
    )


async def handle_admin_action(bot: Bot, message: Message, action: str) -> None:
    language = await get_user_context(message)

    if not await is_admin(message.from_user.id):
        await send_admin_only_message(bot, message, language)
        return

    if action == "admin_stats":
        await bot.send_message(
            message.chat.id, await format_stats_report(language)
        )
        return

    if action == "admin_maintenance":
        await bot.send_message(
            message.chat.id, await format_maintenance_report(language)
        )
        return

    if action == "admin_cleanup_errors":
        await bot.send_message(
            message.chat.id, await cleanup_errors_report(language)
        )
        return

    if action == "admin_cleanup_history":
        await bot.send_message(
            message.chat.id, await cleanup_history_report(language)
        )
        return

    if action == "admin_health":
        await bot.send_message(
            message.chat.id, await format_health_report()
        )
        return

    if action == "admin_reload_admins":
        # reload_admins_report only does in-memory lru_cache.cache_clear() — no DB I/O
        await bot.send_message(message.chat.id, reload_admins_report(language))


async def show_language_menu(bot: Bot, message: Message) -> None:
    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("choose_language", language),
        reply_markup=language_keyboard(),
    )


async def process_music_search(bot: Bot, message: Message) -> None:
    language = await get_user_context(message)

    if not message.text:
        await bot.send_message(message.chat.id, t("please_send_text", language))
        await ask_for_music(bot, message.chat.id, message.from_user.id)
        return

    text = message.text.strip()

    if text.startswith("/"):
        return

    try:
        await send_search_results(
            bot=bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            query=text,
            save_to_history=True,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="music_search",
            error=error,
        )
        await bot.send_message(message.chat.id, t("something_wrong_searching", language))


async def show_favorites(bot: Bot, message: Message) -> None:
    try:
        language = await get_user_context(message)

        await bot.send_message(
            message.chat.id,
            t("favorites_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        tracks = await get_favorite_tracks(message.from_user.id)

        if not tracks:
            await bot.send_message(message.chat.id, t("favorites_empty", language))
            return

        markup = favorites_keyboard(tracks, language)

        await bot.send_message(
            message.chat.id,
            t("favorites_title", language, count=len(tracks)),
            reply_markup=markup,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="favorites",
            error=error,
        )
        language = await get_user_language(message.from_user.id)
        await bot.send_message(message.chat.id, t("could_not_load_favorites", language))


async def show_history(bot: Bot, message: Message) -> None:
    try:
        language = await get_user_context(message)

        await bot.send_message(
            message.chat.id,
            t("history_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        history = await get_search_history(
            message.from_user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            await bot.send_message(message.chat.id, t("history_empty", language))
            return

        markup = history_keyboard(history, language)

        await bot.send_message(
            message.chat.id,
            t("history_title", language, count=len(history)),
            reply_markup=markup,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=message.from_user.id,
            source="history",
            error=error,
        )
        language = await get_user_language(message.from_user.id)
        await bot.send_message(message.chat.id, t("could_not_load_history", language))


# ── simple user commands (7B) ─────────────────────────────────────────────────


@router.message(Command("start"))
async def start_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("welcome", language),
        reply_markup=main_menu_keyboard(language, is_admin=await is_admin(message.from_user.id)),
    )


@router.message(Command("help"))
async def help_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    await bot.send_message(message.chat.id, t("help", language))


@router.message(Command("language"))
async def language_handler(message: Message, bot: Bot) -> None:
    await show_language_menu(bot, message)


@router.message(Command("version"))
async def version_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("version_info", language, version=__version__),
    )


@router.message(Command("favorites"))
async def favorites_handler(message: Message, bot: Bot) -> None:
    await show_favorites(bot, message)


@router.message(Command("history"))
async def history_handler(message: Message, bot: Bot) -> None:
    await show_history(bot, message)


# ── admin commands (7C) ───────────────────────────────────────────────────────


@router.message(Command("errors"))
async def errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(message.chat.id, await format_recent_errors(language))


@router.message(Command("clear_errors"))
async def clear_errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await clear_errors()
    await bot.send_message(message.chat.id, t("errors_cleared", language))


@router.message(Command("health"))
async def health_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(message.chat.id, await format_health_report())


@router.message(Command("stats"))
async def stats_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(message.chat.id, await format_stats_report(language))


@router.message(Command("maintenance"))
async def maintenance_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(
        message.chat.id, await format_maintenance_report(language)
    )


@router.message(Command("cleanup_errors"))
async def cleanup_errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(
        message.chat.id, await cleanup_errors_report(language)
    )


@router.message(Command("cleanup_history"))
async def cleanup_history_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(
        message.chat.id, await cleanup_history_report(language)
    )


@router.message(Command("reload_admins"))
async def reload_admins_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language):
        return

    await bot.send_message(message.chat.id, reload_admins_report(language))


# ── feature commands (7D) ─────────────────────────────────────────────────────


@router.message(Command("similar"))
async def similar_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    last_track_id = await get_last_track_id(message.from_user.id)

    if not last_track_id:
        await bot.send_message(message.chat.id, t("similar_no_context", language))
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
            telegram_id=message.from_user.id,
            source="similar_handler",
            error=error,
        )
        await bot.send_message(message.chat.id, t("similar_empty", language))


@router.message(Command("trending"))
async def trending_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

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
            telegram_id=message.from_user.id,
            source="trending_handler",
            error=error,
        )
        await bot.send_message(message.chat.id, t("trending_empty", language))


# ── text handler (7E) ─────────────────────────────────────────────────────────


@router.message(F.text)
async def text_handler(message: Message, bot: Bot) -> None:
    await upsert_user(message.from_user)

    if message.text and message.text.strip().startswith("/"):
        return

    action = get_menu_action_by_text(message.text)

    if action == "main_menu":
        await show_main_menu(bot, message.chat.id, message.from_user.id)
        return

    if action == "music":
        await ask_for_music(bot, message.chat.id, message.from_user.id)
        return

    if action == "favorites":
        await show_favorites(bot, message)
        return

    if action == "history":
        await show_history(bot, message)
        return

    if action == "language":
        await show_language_menu(bot, message)
        return

    if action == "admin":
        await show_admin_menu(bot, message)
        return

    if action in {
        "admin_stats",
        "admin_maintenance",
        "admin_cleanup_errors",
        "admin_cleanup_history",
        "admin_health",
        "admin_reload_admins",
    }:
        await handle_admin_action(bot, message, action)
        return

    await process_music_search(bot, message)
