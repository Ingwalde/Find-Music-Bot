import sqlite3
from pathlib import Path

from app.config.settings import settings
from app.database.indexes import create_indexes
from app.database.migrations import add_column_if_missing, get_table_columns, migrate_db
from app.database.schema import create_tables
from app.version import __version__


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


def record_schema_version(cursor: sqlite3.Cursor, version: str = __version__) -> None:
    """
    Stores the current application schema version if it is not already recorded.
    """
    cursor.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (version)
        VALUES (?)
        """,
        (version,),
    )


def init_db() -> None:
    """
    Creates all required tables, applies migrations and creates indexes.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        create_tables(cursor)
        migrate_db(cursor)
        create_indexes(cursor)
        record_schema_version(cursor)

        conn.commit()
    finally:
        conn.close()


__all__ = [
    "get_database_path",
    "get_connection",
    "get_table_columns",
    "add_column_if_missing",
    "migrate_db",
    "create_indexes",
    "record_schema_version",
    "init_db",
]
