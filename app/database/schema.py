"""
Database schema definitions for Telegram Music Finder Bot.
"""


async def create_tables_pg(conn) -> None:
    """
    Creates all required tables against PostgreSQL.
    Type notes vs SQLite:
      INTEGER PRIMARY KEY AUTOINCREMENT → BIGSERIAL PRIMARY KEY
      INTEGER (Telegram IDs, FK columns) → BIGINT
      TIMESTAMP DEFAULT CURRENT_TIMESTAMP → TIMESTAMPTZ DEFAULT NOW()
    """
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'en',
            last_track_id TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS searches (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id BIGSERIAL PRIMARY KEY,
            deezer_track_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            artist TEXT,
            album TEXT,
            duration TEXT,
            duration_seconds INTEGER,
            deezer_link TEXT,
            cover_url TEXT,
            release_date TEXT,
            rank INTEGER,
            popularity TEXT,
            spotify_track_id TEXT,
            spotify_link TEXT,
            spotify_updated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            track_id BIGINT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, track_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS errors (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT,
            source TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id BIGSERIAL PRIMARY KEY,
            version TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
