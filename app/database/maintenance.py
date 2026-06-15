from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.database.db import get_connection, get_database_path
from app.version import __version__

DEFAULT_MAINTENANCE_TABLES = (
    "users",
    "searches",
    "tracks",
    "favorites",
    "errors",
    "schema_migrations",
)


def get_maintenance_table_names() -> tuple[str, ...]:
    """
    Returns user-defined SQLite tables visible in maintenance reports.

    The list is discovered from sqlite_master so admin diagnostics stay in sync
    with schema changes without manually updating a hardcoded tuple.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        table_names = tuple(str(row["name"]) for row in cursor.fetchall())
        conn.close()
    except Exception:
        return DEFAULT_MAINTENANCE_TABLES

    return table_names or DEFAULT_MAINTENANCE_TABLES


def format_bytes(size_bytes: int) -> str:
    """
    Formats byte values as a readable size string.
    """
    if size_bytes < 0:
        raise ValueError("size_bytes cannot be negative")

    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} GB"


def get_database_size_bytes(path: str | Path | None = None) -> int:
    """
    Returns SQLite database file size in bytes.
    """
    db_path = Path(path) if path is not None else get_database_path()

    if not db_path.exists():
        return 0

    return db_path.stat().st_size


def get_table_count(table_name: str) -> int:
    """
    Returns row count for a known table.
    """
    if table_name not in get_maintenance_table_names():
        raise ValueError(f"Unsupported table for maintenance stats: {table_name}")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table_name}")
        row = cursor.fetchone()
    finally:
        conn.close()

    return int(row["count"])


def get_table_counts() -> dict[str, int]:
    """
    Returns row counts for maintenance-visible tables.
    """
    return {table_name: get_table_count(table_name) for table_name in get_maintenance_table_names()}


def get_schema_version() -> str:
    """
    Returns latest recorded schema version or current app version as a safe fallback.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT version
            FROM schema_migrations
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()
    except Exception:
        return __version__

    if not row:
        return __version__

    return str(row["version"])


def get_database_summary() -> dict[str, Any]:
    """
    Builds a database maintenance summary used by admin commands.
    """
    size_bytes = get_database_size_bytes()

    return {
        "database_path": str(get_database_path()),
        "database_size_bytes": size_bytes,
        "database_size": format_bytes(size_bytes),
        "table_counts": get_table_counts(),
        "schema_version": get_schema_version(),
        "app_version": __version__,
    }


def cleanup_old_errors(keep_latest: int | None = None) -> dict[str, int]:
    """
    Keeps the newest error rows and removes older saved errors.
    """
    if keep_latest is None:
        keep_latest = settings.ERROR_HISTORY_LIMIT

    if keep_latest < 0:
        raise ValueError("keep_latest cannot be negative")

    before = get_table_count("errors")

    conn = get_connection()
    try:
        cursor = conn.cursor()

        if keep_latest == 0:
            cursor.execute("DELETE FROM errors")
        else:
            cursor.execute(
                """
                DELETE FROM errors
                WHERE id NOT IN (
                    SELECT id
                    FROM errors
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (keep_latest,),
            )

        conn.commit()
    finally:
        conn.close()

    after = get_table_count("errors")

    return {"before": before, "after": after, "deleted": before - after}


def cleanup_search_history(max_rows_per_user: int | None = None) -> dict[str, int]:
    """
    Keeps the newest search rows per user and removes older history entries.
    """
    if max_rows_per_user is None:
        max_rows_per_user = settings.MAX_HISTORY_PER_USER

    if max_rows_per_user < 0:
        raise ValueError("max_rows_per_user cannot be negative")

    before = get_table_count("searches")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users")
        user_ids = [int(row["id"]) for row in cursor.fetchall()]

        for user_id in user_ids:
            if max_rows_per_user == 0:
                cursor.execute("DELETE FROM searches WHERE user_id = ?", (user_id,))
                continue

            cursor.execute(
                """
                DELETE FROM searches
                WHERE user_id = ?
                AND id NOT IN (
                    SELECT id
                    FROM searches
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (user_id, user_id, max_rows_per_user),
            )

        conn.commit()
    finally:
        conn.close()

    after = get_table_count("searches")

    return {"before": before, "after": after, "deleted": before - after}
