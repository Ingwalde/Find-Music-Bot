def row_to_dict(row) -> dict:
    """
    Converts a database row to dict.
    """
    return dict(row) if row else {}
