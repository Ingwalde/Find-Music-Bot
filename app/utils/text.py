def truncate_text(text: str, max_length: int = 64) -> str:
    """
    Truncates long text for Telegram buttons.
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """
    Splits long Telegram messages into smaller chunks.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []

    for index in range(0, len(text), max_length):
        chunks.append(text[index:index + max_length])

    return chunks
