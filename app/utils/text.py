ELLIPSIS = "..."


def truncate_text(text: str, max_length: int = 64) -> str:
    """
    Truncates long text for Telegram buttons, never returning more than
    max_length characters.

    Below len(ELLIPSIS) there is no room for the marker, so the text is cut
    outright. Without that branch, text[: max_length - 3] took a negative
    index and returned a *longer* string than asked for:
    truncate_text("abcdefghij", 0) produced "abcdefg..." — ten characters for
    a limit of zero. The property test's min_value=4 hid it by starting above
    the broken range.
    """
    if max_length <= 0:
        return ""

    if len(text) <= max_length:
        return text

    if max_length <= len(ELLIPSIS):
        return text[:max_length]

    return text[: max_length - len(ELLIPSIS)] + ELLIPSIS


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
