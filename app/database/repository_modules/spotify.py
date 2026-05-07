from app.database.db import get_connection


def get_spotify_data_by_deezer_id(deezer_track_id: str | int) -> dict | None:
    """
    Returns cached Spotify data for a Deezer track.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT spotify_track_id, spotify_link, spotify_updated_at
        FROM tracks
        WHERE deezer_track_id = ?
        LIMIT 1
        """,
        (str(deezer_track_id),),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    spotify_link = row["spotify_link"]

    if not spotify_link:
        return None

    return {
        "spotify_track_id": row["spotify_track_id"],
        "spotify_link": spotify_link,
        "spotify_updated_at": row["spotify_updated_at"],
    }


def update_spotify_data_for_track(
    deezer_track_id: str | int,
    spotify_track_id: str,
    spotify_link: str,
) -> None:
    """
    Updates cached Spotify metadata for an existing Deezer track.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tracks
        SET
            spotify_track_id = ?,
            spotify_link = ?,
            spotify_updated_at = CURRENT_TIMESTAMP
        WHERE deezer_track_id = ?
        """,
        (
            spotify_track_id,
            spotify_link,
            str(deezer_track_id),
        ),
    )

    conn.commit()
    conn.close()
