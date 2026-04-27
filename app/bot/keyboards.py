from telebot import types
from app.bot.messages import BACK_TO_MENU_TEXT
from app.utils.text import truncate_text


def main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("music"))
    markup.add(
        types.KeyboardButton("favorites"),
        types.KeyboardButton("history"),
    )
    return markup

def search_mode_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Keyboard shown during music search.
    Main menu buttons are hidden here.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(BACK_TO_MENU_TEXT))
    return markup

def remove_keyboard() -> types.ReplyKeyboardRemove:
    """
    Removes bottom reply keyboard.
    """
    return types.ReplyKeyboardRemove()


def search_results_keyboard(tracks: list[dict]) -> types.InlineKeyboardMarkup:
    """
    Creates inline keyboard with Deezer search results.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")

        button_text = truncate_text(f"{title} — {artist}", 64)

        markup.add(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"track:{track_id}",
            )
        )

    return markup


def track_actions_keyboard(
    track: dict,
    is_favorite: bool = False,
) -> types.InlineKeyboardMarkup:
    """
    Creates inline keyboard under selected track card.
    Deezer is displayed as URL button.
    Favorite button changes depending on current status.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    deezer_link = track.get("deezer_link")
    track_id = track.get("deezer_track_id")

    if deezer_link:
        markup.add(
            types.InlineKeyboardButton(
                text="🎧 Deezer",
                url=deezer_link,
            )
        )

    if is_favorite:
        favorite_button = types.InlineKeyboardButton(
            text="❌ Remove from favorites",
            callback_data=f"unfav:{track_id}",
        )
    else:
        favorite_button = types.InlineKeyboardButton(
            text="⭐ Add to favorites",
            callback_data=f"fav:{track_id}",
        )

    markup.add(
        types.InlineKeyboardButton(
            text="📖 Lyrics",
            callback_data=f"lyrics:{track_id}",
        ),
        favorite_button,
    )

    markup.add(
        types.InlineKeyboardButton(
            text="🔎 Search again",
            callback_data="search_again",
        )
    )

    return markup


def genius_url_keyboard(url: str) -> types.InlineKeyboardMarkup:
    """
    Creates button for opening Genius lyrics page.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text="📖 Open lyrics on Genius",
            url=url,
        )
    )
    return markup


def favorites_keyboard(tracks: list[dict]) -> types.InlineKeyboardMarkup:
    """
    Creates inline keyboard with user's favorite tracks.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")

        button_text = truncate_text(f"🎵 {title} — {artist}", 64)

        markup.add(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"track:{track_id}",
            )
        )

    return markup
