"""baseline schema

Revision ID: bf5069cbb1be
Revises:
Create Date: 2026-06-18 11:20:22.051685

Raw-SQL baseline — mirrors app.database.schema.create_tables_pg and
app.database.indexes.create_indexes_pg exactly (same tables, columns,
types, constraints, and indexes). No SQLAlchemy ORM/Core models are used;
this project's application runtime stays on asyncpg.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bf5069cbb1be'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id BIGSERIAL PRIMARY KEY,
            version TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_searches_user_id_id ON searches(user_id, id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_deezer_track_id ON tracks(deezer_track_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_spotify_track_id ON tracks(spotify_track_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_track_id ON favorites(track_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_errors_created_at")
    op.execute("DROP INDEX IF EXISTS idx_favorites_track_id")
    op.execute("DROP INDEX IF EXISTS idx_favorites_user_id")
    op.execute("DROP INDEX IF EXISTS idx_tracks_spotify_track_id")
    op.execute("DROP INDEX IF EXISTS idx_tracks_deezer_track_id")
    op.execute("DROP INDEX IF EXISTS idx_searches_user_id_id")
    op.execute("DROP INDEX IF EXISTS idx_searches_user_id")
    op.execute("DROP INDEX IF EXISTS idx_users_telegram_id")

    op.execute("DROP TABLE IF EXISTS schema_migrations")
    op.execute("DROP TABLE IF EXISTS errors")
    op.execute("DROP TABLE IF EXISTS favorites")
    op.execute("DROP TABLE IF EXISTS tracks")
    op.execute("DROP TABLE IF EXISTS searches")
    op.execute("DROP TABLE IF EXISTS users")
