from aiogram import Bot, Router
from aiogram.types import CallbackQuery

from app.bot.actions import ask_for_music, show_main_menu
from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_FAVORITES_CLEAR_CANCEL,
    ACTION_FAVORITES_CLEAR_CONFIRM,
    ACTION_FAVORITES_CLEAR_REQUEST,
    ACTION_HISTORY_CLEAR_CANCEL,
    ACTION_HISTORY_CLEAR_CONFIRM,
    ACTION_HISTORY_CLEAR_REQUEST,
    ACTION_MAIN_MENU,
    ACTION_NOOP,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_HISTORY,
    CB_LANGUAGE,
    CB_LYRICS,
    CB_PAGE,
    CB_SIMILAR,
    CB_TRACK,
    CB_UNFAVORITE,
)
from app.bot.favorites_callbacks import (
    handle_clear_favorites_cancel_callback,
    handle_clear_favorites_confirm_callback,
    handle_clear_favorites_request_callback,
    handle_favorite_callback,
    handle_remove_favorite_callback,
)
from app.bot.history_callbacks import (
    handle_clear_history_cancel_callback,
    handle_clear_history_confirm_callback,
    handle_clear_history_request_callback,
    handle_history_search_callback,
)
from app.bot.language_callbacks import handle_language_callback
from app.bot.lyrics_callbacks import handle_lyrics_callback
from app.bot.pagination_callbacks import (
    handle_back_to_results_callback,
    handle_page_callback,
)
from app.bot.similar_callbacks import handle_similar_callback
from app.bot.track_callbacks import handle_track_callback
from app.database.repositories import get_user_language
from app.localization.translations import t

router = Router(name="callbacks")


@router.callback_query()
async def callback_router(call: CallbackQuery, bot: Bot) -> None:
    # from_user is Optional on the aiogram type but Telegram always populates
    # it for callback queries; guard rather than assume, since the very next
    # line dereferences it.
    if call.from_user is None:
        await bot.answer_callback_query(call.id)
        return

    data = call.data or ""
    language = await get_user_language(call.from_user.id)

    # Telegram omits `message` entirely once the message carrying the button is
    # older than ~48h, so this is None for a user tapping a button on last
    # week's track card. Every downstream handler reads message.chat.id, which
    # would raise AttributeError, get swallowed by its own except Exception,
    # and surface as a generic failure. Guarding here covers all of them.
    if call.message is None:
        await bot.answer_callback_query(
            call.id, t("search_session_expired", language), show_alert=True
        )
        return

    try:
        if data.startswith(f"{CB_LANGUAGE}:"):
            language_code = data.split(":", 1)[1]
            await handle_language_callback(bot, call, language_code, language)
            return

        if data.startswith(f"{CB_TRACK}:"):
            track_id = data.split(":", 1)[1]
            await handle_track_callback(bot, call, track_id, language)
            return

        if data.startswith(f"{CB_PAGE}:"):
            page = int(data.split(":", 1)[1])
            await handle_page_callback(bot, call, page, language)
            return

        if data == ACTION_BACK_RESULTS:
            await handle_back_to_results_callback(bot, call, language)
            return

        if data.startswith(f"{CB_FAVORITE}:"):
            track_id = data.split(":", 1)[1]
            await handle_favorite_callback(bot, call, track_id, language)
            return

        if data.startswith(f"{CB_UNFAVORITE}:"):
            track_id = data.split(":", 1)[1]
            await handle_remove_favorite_callback(bot, call, track_id, language)
            return

        if data == ACTION_FAVORITES_CLEAR_REQUEST:
            await handle_clear_favorites_request_callback(bot, call, language)
            return

        if data == ACTION_FAVORITES_CLEAR_CONFIRM:
            await handle_clear_favorites_confirm_callback(bot, call, language)
            return

        if data == ACTION_FAVORITES_CLEAR_CANCEL:
            await handle_clear_favorites_cancel_callback(bot, call, language)
            return

        if data.startswith(f"{CB_LYRICS}:"):
            track_id = data.split(":", 1)[1]
            await handle_lyrics_callback(bot, call, track_id, language)
            return

        if data.startswith(f"{CB_SIMILAR}:"):
            track_id = data.split(":", 1)[1]
            await handle_similar_callback(bot, call, track_id, language)
            return

        if data.startswith(f"{CB_HISTORY}:"):
            search_id = data.split(":", 1)[1]
            await handle_history_search_callback(bot, call, search_id, language)
            return

        if data == ACTION_HISTORY_CLEAR_REQUEST:
            await handle_clear_history_request_callback(bot, call, language)
            return

        if data == ACTION_HISTORY_CLEAR_CONFIRM:
            await handle_clear_history_confirm_callback(bot, call, language)
            return

        if data == ACTION_HISTORY_CLEAR_CANCEL:
            await handle_clear_history_cancel_callback(bot, call, language)
            return

        if data == ACTION_MAIN_MENU:
            await bot.answer_callback_query(call.id)
            await show_main_menu(bot, call.message.chat.id, call.from_user.id)
            return

        if data == ACTION_SEARCH_AGAIN:
            await bot.answer_callback_query(call.id)
            await ask_for_music(bot, call.message.chat.id, call.from_user.id)
            return

        if data == ACTION_NOOP:
            await bot.answer_callback_query(call.id)
            return
    except (IndexError, ValueError):
        # Malformed/stale callback_data (missing the expected ":" suffix, or a
        # non-numeric CB_PAGE value) — answer like any other unrecognized
        # action instead of raising past the dispatcher.
        await bot.answer_callback_query(
            call.id,
            t("unknown_action", language),
            show_alert=False,
        )
        return

    await bot.answer_callback_query(
        call.id,
        t("unknown_action", language),
        show_alert=False,
    )
