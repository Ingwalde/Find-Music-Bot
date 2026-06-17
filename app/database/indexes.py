"""
Database indexes used by the bot.
"""


async def create_indexes_pg(conn) -> None:
    """
    Creates indexes for faster common queries against PostgreSQL.
    """
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id_id ON searches(user_id, id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_deezer_track_id ON tracks(deezer_track_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_spotify_track_id ON tracks(spotify_track_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_track_id ON favorites(track_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at)"
    )
