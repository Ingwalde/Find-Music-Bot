import telebot
from telebot import types

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
from app.bot.track_callbacks import handle_track_callback
from app.database.repositories import get_user_language
from app.localization.translations import t


def register_callbacks(bot: telebot.TeleBot) -> None:
    """
    Registers all callback query handlers.
    """

    @bot.callback_query_handler(func=lambda call: True)
    def callback_router(call: types.CallbackQuery) -> None:
        data = call.data or ""
        language = get_user_language(call.from_user.id)

        if data.startswith(f"{CB_LANGUAGE}:"):
            language_code = data.split(":", 1)[1]
            handle_language_callback(bot, call, language_code)
            return

        if data.startswith(f"{CB_TRACK}:"):
            track_id = data.split(":", 1)[1]
            handle_track_callback(bot, call, track_id)
            return

        if data.startswith(f"{CB_PAGE}:"):
            page = int(data.split(":", 1)[1])
            handle_page_callback(bot, call, page)
            return

        if data == ACTION_BACK_RESULTS:
            handle_back_to_results_callback(bot, call)
            return

        if data.startswith(f"{CB_FAVORITE}:"):
            track_id = data.split(":", 1)[1]
            handle_favorite_callback(bot, call, track_id)
            return

        if data.startswith(f"{CB_UNFAVORITE}:"):
            track_id = data.split(":", 1)[1]
            handle_remove_favorite_callback(bot, call, track_id)
            return

        if data == ACTION_FAVORITES_CLEAR_REQUEST:
            handle_clear_favorites_request_callback(bot, call)
            return

        if data == ACTION_FAVORITES_CLEAR_CONFIRM:
            handle_clear_favorites_confirm_callback(bot, call)
            return

        if data == ACTION_FAVORITES_CLEAR_CANCEL:
            handle_clear_favorites_cancel_callback(bot, call)
            return

        if data.startswith(f"{CB_LYRICS}:"):
            track_id = data.split(":", 1)[1]
            handle_lyrics_callback(bot, call, track_id)
            return

        if data.startswith(f"{CB_HISTORY}:"):
            search_id = data.split(":", 1)[1]
            handle_history_search_callback(bot, call, search_id)
            return

        if data == ACTION_HISTORY_CLEAR_REQUEST:
            handle_clear_history_request_callback(bot, call)
            return

        if data == ACTION_HISTORY_CLEAR_CONFIRM:
            handle_clear_history_confirm_callback(bot, call)
            return

        if data == ACTION_HISTORY_CLEAR_CANCEL:
            handle_clear_history_cancel_callback(bot, call)
            return

        if data == ACTION_MAIN_MENU:
            bot.answer_callback_query(call.id)
            show_main_menu(bot, call.message.chat.id, call.from_user.id)
            return

        if data == ACTION_SEARCH_AGAIN:
            bot.answer_callback_query(call.id)
            ask_for_music(bot, call.message.chat.id, call.from_user.id)
            return

        if data == ACTION_NOOP:
            bot.answer_callback_query(call.id)
            return

        bot.answer_callback_query(
            call.id,
            t("unknown_action", language),
            show_alert=False,
        )
