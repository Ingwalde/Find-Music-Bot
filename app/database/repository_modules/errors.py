from app.database.db import get_connection
from app.database.repository_modules.common import row_to_dict


def save_error(
    telegram_id: int | None,
    source: str,
    error_message: str,
) -> None:
    """
    Saves error to database.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO errors (telegram_id, source, error_message)
        VALUES (?, ?, ?)
        """,
        (telegram_id, source, error_message),
    )

    conn.commit()
    conn.close()


def get_recent_errors(limit: int = 10) -> list[dict]:
    """
    Returns recent saved errors.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT telegram_id, source, error_message, created_at
        FROM errors
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [row_to_dict(row) for row in rows]


def clear_errors() -> None:
    """
    Clears saved errors.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM errors")

    conn.commit()
    conn.close()
