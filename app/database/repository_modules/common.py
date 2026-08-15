from typing import Any


def row_to_dict(row: Any) -> dict:
    """
    Converts a database row to dict.

    Typed as Any rather than asyncpg.Record: callers also pass None (handled
    by the falsy branch) and plain mappings in tests.
    """
    return dict(row) if row else {}
