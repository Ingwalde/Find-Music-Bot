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
    Returns existing column names for selected table.
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
    Adds a new column to an existing SQLite table if it does not exist.
    Used for simple local development migrations.
    """
    columns = get_table_columns(cursor, table_name)

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def migrate_db(cursor: sqlite3.Cursor) -> None:
    """
    Applies simple migrations for old local databases.
    """
    add_column_if_missing(cursor, "tracks", "release_date", "TEXT")
    add_column_if_missing(cursor, "tracks", "rank", "INTEGER")
    add_column_if_missing(cursor, "tracks", "popularity", "TEXT")


def init_db() -> None:
    """
    Creates all required tables.
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    conn.commit()
    conn.close()
