import telebot
from telebot import types

from app.bot.actions import send_track_card
from app.database.repositories import save_track
from app.services.deezer_service import get_track
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def handle_track_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Handles selected track button.
    """
    try:
        bot.answer_callback_query(call.id)

        track = get_track(track_id)
        save_track(track)

        send_track_card(
            bot=bot,
            chat_id=call.message.chat.id,
            telegram_id=call.from_user.id,
            track=track,
        )

    except Exception as error:
        log_and_save_error(logger, call.from_user.id, "track_callback", error)
        bot.send_message(
            call.message.chat.id,
            "Could not load track information.",
        )
