from app.database.db import get_connection
from app.database.repository_modules.common import row_to_dict


def save_track(track: dict) -> int:
    """
    Saves track to database and returns internal track ID.
    Updates cached metadata when the same Deezer track already exists.
    """
    conn = get_connection()
    try:
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
                cover_url,
                release_date,
                rank,
                popularity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(deezer_track_id)
            DO UPDATE SET
                title = excluded.title,
                artist = excluded.artist,
                album = excluded.album,
                duration = excluded.duration,
                duration_seconds = excluded.duration_seconds,
                deezer_link = excluded.deezer_link,
                cover_url = excluded.cover_url,
                release_date = excluded.release_date,
                rank = excluded.rank,
                popularity = excluded.popularity,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                str(track.get("deezer_track_id")),
                track.get("title"),
                track.get("artist"),
                track.get("album"),
                track.get("duration"),
                track.get("duration_seconds"),
                track.get("deezer_link"),
                track.get("cover_url"),
                track.get("release_date"),
                track.get("rank"),
                track.get("popularity"),
            ),
        )

        conn.commit()

        cursor.execute(
            """
            SELECT id FROM tracks
            WHERE deezer_track_id = ?
            """,
            (str(track.get("deezer_track_id")),),
        )

        row = cursor.fetchone()
    finally:
        conn.close()

    return int(row["id"])


def get_tracks_by_artist(
    artist: str,
    exclude_deezer_id: str,
    limit: int = 3,
) -> list[dict]:
    """
    Returns cached tracks by artist from local DB, excluding the given track.
    Ordered by rank descending so the most popular tracks appear first.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deezer_track_id, title, artist, album, duration, deezer_link, cover_url
            FROM tracks
            WHERE artist = ? AND deezer_track_id != ?
            ORDER BY rank DESC
            LIMIT ?
            """,
            (artist, str(exclude_deezer_id), limit),
        )

        rows = cursor.fetchall()
    finally:
        conn.close()

    return [row_to_dict(row) for row in rows]


def get_track_by_deezer_id(deezer_track_id: str | int) -> dict | None:
    """
    Returns cached track by Deezer ID from SQLite.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                deezer_track_id,
                title,
                artist,
                album,
                duration,
                duration_seconds,
                deezer_link,
                cover_url,
                release_date,
                rank,
                popularity,
                spotify_track_id,
                spotify_link,
                spotify_updated_at,
                created_at,
                updated_at
            FROM tracks
            WHERE deezer_track_id = ?
            LIMIT 1
            """,
            (str(deezer_track_id),),
        )

        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return row_to_dict(row)
