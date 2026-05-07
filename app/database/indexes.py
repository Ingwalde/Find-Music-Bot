"""
SQLite indexes used by the bot.
"""

import sqlite3


def create_indexes(cursor: sqlite3.Cursor) -> None:
    """
    Creates indexes for faster common queries.
    """
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id_id ON searches(user_id, id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_deezer_track_id ON tracks(deezer_track_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_spotify_track_id ON tracks(spotify_track_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_track_id ON favorites(track_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at)"
    )
