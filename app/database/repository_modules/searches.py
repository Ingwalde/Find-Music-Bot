from app.config.settings import settings
from app.database.db import get_connection
from app.database.repository_modules.common import row_to_dict
from app.database.repository_modules.users import get_user_id


def trim_search_history(telegram_id: int) -> None:
    """
    Keeps only newest MAX_HISTORY_PER_USER search rows for current user.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()

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
            (user_id, user_id, settings.MAX_HISTORY_PER_USER),
        )

        conn.commit()
    finally:
        conn.close()


def save_search(telegram_id: int, query: str) -> None:
    """
    Saves user's search query and trims old history rows.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    normalized_query = query.strip()

    if not normalized_query:
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO searches (user_id, query)
            VALUES (?, ?)
            """,
            (user_id, normalized_query),
        )

        conn.commit()
    finally:
        conn.close()

    trim_search_history(telegram_id)


def get_search_history(telegram_id: int, limit: int = 10) -> list[dict]:
    """
    Returns recent unique search queries for user.
    The latest duplicate query is kept and older duplicates are hidden.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.id, s.query, s.created_at
            FROM searches s
            JOIN (
                SELECT LOWER(TRIM(query)) AS normalized_query, MAX(id) AS latest_id
                FROM searches
                WHERE user_id = ?
                GROUP BY LOWER(TRIM(query))
            ) latest ON s.id = latest.latest_id
            WHERE s.user_id = ?
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (user_id, user_id, limit),
        )

        rows = cursor.fetchall()
    finally:
        conn.close()

    return [row_to_dict(row) for row in rows]


def get_search_query_by_id(telegram_id: int, search_id: int) -> str | None:
    """
    Returns search query by history ID.
    Checks that the history item belongs to the current user.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return None

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT query
            FROM searches
            WHERE id = ?
            AND user_id = ?
            LIMIT 1
            """,
            (search_id, user_id),
        )

        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return str(row["query"])


def clear_search_history(telegram_id: int) -> None:
    """
    Clears current user's search history.
    """
    user_id = get_user_id(telegram_id)

    if not user_id:
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM searches
            WHERE user_id = ?
            """,
            (user_id,),
        )

        conn.commit()
    finally:
        conn.close()
