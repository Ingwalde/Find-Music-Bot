import pytest

from app.database.maintenance import format_bytes


def test_format_bytes_formats_expected_units():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"

    with pytest.raises(ValueError):
        format_bytes(-1)
