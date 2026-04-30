from app.utils.text import split_long_message, truncate_text


def test_truncate_text_keeps_short_text():
    assert truncate_text("Short text", 64) == "Short text"


def test_truncate_text_truncates_long_text():
    text = "A" * 80

    result = truncate_text(text, max_length=20)

    assert len(result) == 20
    assert result.endswith("...")


def test_split_long_message_keeps_short_message():
    assert split_long_message("hello", max_length=10) == ["hello"]


def test_split_long_message_splits_long_message():
    chunks = split_long_message("abcdefghij", max_length=4)

    assert chunks == ["abcd", "efgh", "ij"]
