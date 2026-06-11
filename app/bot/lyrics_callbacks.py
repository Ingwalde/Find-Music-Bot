import telebot
from telebot import types

from app.bot.keyboards import genius_url_keyboard
from app.database.repositories import get_user_language
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.services.lyrics_service import find_lyrics_url
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_lyrics_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Finds Genius lyrics page for selected track.
    """
    language = get_user_language(call.from_user.id)
    bot.answer_callback_query(call.id)

    try:
        track = get_track(track_id)
        lyrics_url = find_lyrics_url(
            title=track["title"],
            artist=track["artist"],
        )
    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "lyrics_callback", error)
        bot.send_message(call.message.chat.id, t("genius_error", language))
        return

    if not lyrics_url:
        bot.send_message(call.message.chat.id, t("lyrics_not_found", language))
        return

    bot.send_message(
        call.message.chat.id,
        t("lyrics_page_found", language),
        reply_markup=genius_url_keyboard(lyrics_url, language),
    )
