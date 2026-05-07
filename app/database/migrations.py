"""
Lightweight SQLite migrations.

The project uses local SQLite, so migrations are intentionally simple:
missing columns are added during startup. This keeps older local databases compatible
with newer versions of the bot.
"""

import sqlite3


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

    add_column_if_missing(cursor, "tracks", "spotify_track_id", "TEXT")
    add_column_if_missing(cursor, "tracks", "spotify_link", "TEXT")
    add_column_if_missing(cursor, "tracks", "spotify_updated_at", "TIMESTAMP")
