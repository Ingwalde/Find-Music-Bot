def row_to_dict(row) -> dict:
    """
    Converts sqlite row to dict.
    """
    return dict(row) if row else {}
