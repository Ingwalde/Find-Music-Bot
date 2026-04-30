import telebot
from telebot import types

from app.bot.keyboards import genius_url_keyboard
from app.bot.messages import GENIUS_ERROR_TEXT, LYRICS_NOT_FOUND_TEXT
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
    try:
        bot.answer_callback_query(call.id, "Searching lyrics...")

        track = get_track(track_id)

        lyrics_url = find_lyrics_url(
            title=track["title"],
            artist=track["artist"],
        )

        if not lyrics_url:
            bot.send_message(call.message.chat.id, LYRICS_NOT_FOUND_TEXT)
            return

        bot.send_message(
            call.message.chat.id,
            "Lyrics page found:",
            reply_markup=genius_url_keyboard(lyrics_url),
        )

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "lyrics_callback", error)
        bot.send_message(call.message.chat.id, GENIUS_ERROR_TEXT)
