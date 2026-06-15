from app.database.db import get_connection
from app.database.repository_modules.common import row_to_dict
from app.database.repository_modules.tracks import save_track
from app.database.repository_modules.users import get_user_id


def add_favorite(telegram_id: int, track: dict) -> None:
    """
    Adds selected track to user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    track_id = save_track(track)

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO favorites (user_id, track_id)
            VALUES (?, ?)
            """,
            (user_id, track_id),
        )

        conn.commit()
    finally:
        conn.close()


def remove_favorite(telegram_id: int, deezer_track_id: str) -> None:
    """
    Removes selected track from user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    try:
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
    finally:
        conn.close()


def clear_favorites(telegram_id: int) -> None:
    """
    Removes all favorite tracks for current user.
    Tracks remain saved in the tracks table as cache.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM favorites
            WHERE user_id = ?
            """,
            (user_id,),
        )

        conn.commit()
    finally:
        conn.close()


def is_track_favorite(telegram_id: int, deezer_track_id: str) -> bool:
    """
    Checks if selected track is already in user's favorites.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return False

    conn = get_connection()
    try:
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
    finally:
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
    try:
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
                tracks.release_date,
                tracks.rank,
                tracks.popularity,
                tracks.spotify_track_id,
                tracks.spotify_link,
                tracks.spotify_updated_at,
                tracks.created_at,
                tracks.updated_at,
                favorites.created_at AS favorite_created_at
            FROM favorites
            JOIN tracks ON favorites.track_id = tracks.id
            WHERE favorites.user_id = ?
            ORDER BY favorites.created_at DESC
            """,
            (user_id,),
        )

        rows = cursor.fetchall()
    finally:
        conn.close()

    return [row_to_dict(row) for row in rows]
