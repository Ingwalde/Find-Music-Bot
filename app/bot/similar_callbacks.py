import telebot
from telebot import types

from app.database.repositories import get_user_language
from app.localization.translations import t
from app.services.deezer_service import get_track
from app.services.recommendations_service import format_similar_text, get_similar_by_genre
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_similar_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    track_id: str,
) -> None:
    """
    Handles the 🎯 Similar button — fetches and displays tracks similar to
    the selected track using the Deezer radio endpoint.
    """
    language = get_user_language(call.from_user.id)
    bot.answer_callback_query(call.id)

    source_track = None
    try:
        try:
            source_track = get_track(track_id)
            header = t(
                "similar_header",
                language,
                title=source_track.get("title", ""),
                artist=source_track.get("artist", ""),
            )
        except Exception:
            header = t("similar_header", language, title="", artist="").rstrip(" —").rstrip()

        artist_name = source_track.get("artist", "") if source_track else ""
        tracks = get_similar_by_genre(track_id, artist_name=artist_name)

        if not tracks:
            bot.send_message(call.message.chat.id, t("similar_empty", language))
            return

        text = format_similar_text(header, tracks[:5], artist_name)
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as error:
        log_and_save_error(
            logger=logger,
            telegram_id=call.from_user.id,
            source="similar_callback",
            error=error,
        )
        bot.send_message(call.message.chat.id, t("similar_empty", language))
