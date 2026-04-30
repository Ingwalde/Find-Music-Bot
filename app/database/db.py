import sqlite3
from pathlib import Path

from app.config.settings import settings


def get_database_path() -> Path:
    """
    Returns database path and creates parent directory if needed.
    """
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    """
    Creates SQLite connection.
    """
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    """
    Returns existing table columns.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return {row[1] for row in rows}


def add_column_if_missing(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    """
    Adds a column to an existing SQLite table if it does not exist.
    """
    columns = get_table_columns(cursor, table_name)

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def migrate_db(cursor: sqlite3.Cursor) -> None:
    """
    Applies lightweight migrations for existing local databases.
    """
    add_column_if_missing(cursor, "users", "language", "TEXT DEFAULT 'en'")
    add_column_if_missing(cursor, "tracks", "release_date", "TEXT")
    add_column_if_missing(cursor, "tracks", "rank", "INTEGER")
    add_column_if_missing(cursor, "tracks", "popularity", "TEXT")
    add_column_if_missing(cursor, "tracks", "updated_at", "TIMESTAMP")


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
        "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_favorites_track_id ON favorites(track_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at)"
    )


def init_db() -> None:
    """
    Creates all required tables, applies migrations and creates indexes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, track_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            source TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    migrate_db(cursor)
    create_indexes(cursor)

    conn.commit()
    conn.close()
