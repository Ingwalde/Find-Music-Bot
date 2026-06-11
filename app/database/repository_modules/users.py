from telebot.types import User

from app.database.db import get_connection
from app.localization.languages import DEFAULT_LANGUAGE, is_supported_language


def upsert_user(user: User) -> None:
    """
    Saves Telegram user or updates existing one.
    Existing language is preserved.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
        """,
        (user.id, user.username, user.first_name),
    )

    conn.commit()
    conn.close()


def get_user_id(telegram_id: int) -> int | None:
    """
    Returns internal database user ID by Telegram ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return int(row["id"])


def get_user_language(telegram_id: int | None) -> str:
    """
    Returns user's selected language.
    English is used as default/fallback.
    """
    if not telegram_id:
        return DEFAULT_LANGUAGE

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT language
        FROM users
        WHERE telegram_id = ?
        LIMIT 1
        """,
        (telegram_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return DEFAULT_LANGUAGE

    language = row["language"] or DEFAULT_LANGUAGE

    if not is_supported_language(language):
        return DEFAULT_LANGUAGE

    return language


def set_user_language(telegram_id: int, language: str) -> None:
    """
    Saves user's selected language.
    """
    if not is_supported_language(language):
        language = DEFAULT_LANGUAGE

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
        """,
        (language, telegram_id),
    )

    conn.commit()
    conn.close()


def save_last_track_id(telegram_id: int, deezer_track_id: str) -> None:
    """
    Saves last viewed Deezer track ID for the user.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_track_id = ?
        WHERE telegram_id = ?
        """,
        (str(deezer_track_id), telegram_id),
    )

    conn.commit()
    conn.close()


def get_last_track_id(telegram_id: int) -> str | None:
    """
    Returns last viewed Deezer track ID for the user.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT last_track_id
        FROM users
        WHERE telegram_id = ?
        LIMIT 1
        """,
        (telegram_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return row["last_track_id"]
