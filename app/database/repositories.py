from telebot.types import User

from app.database.db import get_connection


def row_to_dict(row) -> dict:
    """
    Converts sqlite row to dict.
    """
    return dict(row) if row else {}


def upsert_user(user: User) -> None:
    """
    Saves Telegram user or updates existing one.
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


def save_search(telegram_id: int, query: str) -> None:
    """
    Saves user's search query.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO searches (user_id, query)
        VALUES (?, ?)
        """,
        (user_id, query),
    )

    conn.commit()
    conn.close()


def save_track(track: dict) -> int:
    """
    Saves track to database and returns internal track ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tracks (
            deezer_track_id,
            title,
            artist,
            album,
            duration,
            duration_seconds,
            deezer_link,
            cover_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(deezer_track_id)
        DO UPDATE SET
            title = excluded.title,
            artist = excluded.artist,
            album = excluded.album,
            duration = excluded.duration,
            duration_seconds = excluded.duration_seconds,
            deezer_link = excluded.deezer_link,
            cover_url = excluded.cover_url
        """,
        (
            track.get("deezer_track_id"),
            track.get("title"),
            track.get("artist"),
            track.get("album"),
            track.get("duration"),
            track.get("duration_seconds"),
            track.get("deezer_link"),
            track.get("cover_url"),
        ),
    )

    conn.commit()

    cursor.execute(
        """
        SELECT id FROM tracks
        WHERE deezer_track_id = ?
        """,
        (track.get("deezer_track_id"),),
    )

    row = cursor.fetchone()
    conn.close()

    return int(row["id"])


def add_favorite(telegram_id: int, track: dict) -> None:
    """
    Adds selected track to user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    track_id = save_track(track)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO favorites (user_id, track_id)
        VALUES (?, ?)
        """,
        (user_id, track_id),
    )

    conn.commit()
    conn.close()


def remove_favorite(telegram_id: int, deezer_track_id: str) -> None:
    """
    Removes selected track from user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM favorites
        WHERE user_id = ?
        AND track_id = (
            SELECT id FROM tracks
            WHERE deezer_track_id = ?
            LIMIT 1
        )
        """,
        (user_id, str(deezer_track_id)),
    )

    conn.commit()
    conn.close()


def is_track_favorite(telegram_id: int, deezer_track_id: str) -> bool:
    """
    Checks if selected track is already in user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT favorites.id
        FROM favorites
        JOIN tracks ON favorites.track_id = tracks.id
        WHERE favorites.user_id = ?
        AND tracks.deezer_track_id = ?
        LIMIT 1
        """,
        (user_id, str(deezer_track_id)),
    )

    row = cursor.fetchone()
    conn.close()

    return row is not None


def get_favorite_tracks(telegram_id: int) -> list[dict]:
    """
    Returns user's favorite tracks.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            tracks.deezer_track_id,
            tracks.title,
            tracks.artist,
            tracks.album,
            tracks.duration,
            tracks.duration_seconds,
            tracks.deezer_link,
            tracks.cover_url,
            favorites.created_at
        FROM favorites
        JOIN tracks ON favorites.track_id = tracks.id
        WHERE favorites.user_id = ?
        ORDER BY favorites.created_at DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [row_to_dict(row) for row in rows]


def get_search_history(telegram_id: int, limit: int = 10) -> list[dict]:
    """
    Returns recent unique search queries for user.
    The latest duplicate query is kept and older duplicates are hidden.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s.id, s.query, s.created_at
        FROM searches s
        JOIN (
            SELECT LOWER(TRIM(query)) AS normalized_query, MAX(id) AS latest_id
            FROM searches
            WHERE user_id = ?
            GROUP BY LOWER(TRIM(query))
        ) latest ON s.id = latest.latest_id
        WHERE s.user_id = ?
        ORDER BY s.id DESC
        LIMIT ?
        """,
        (user_id, user_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [row_to_dict(row) for row in rows]


def get_search_query_by_id(telegram_id: int, search_id: int) -> str | None:
    """
    Returns search query by history ID.
    Checks that the history item belongs to the current user.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT query
        FROM searches
        WHERE id = ?
        AND user_id = ?
        LIMIT 1
        """,
        (search_id, user_id),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return str(row["query"])


def clear_search_history(telegram_id: int) -> None:
    """
    Clears current user's search history.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM searches
        WHERE user_id = ?
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


def save_error(
    telegram_id: int | None,
    source: str,
    error_message: str,
) -> None:
    """
    Saves error to database.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO errors (telegram_id, source, error_message)
        VALUES (?, ?, ?)
        """,
        (telegram_id, source, error_message),
    )

    conn.commit()
    conn.close()
