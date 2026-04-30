import pytest

from app.utils.time import convert_duration


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00"),
        (5, "00:05"),
        (65, "01:05"),
        (240, "04:00"),
        (3605, "01:00:05"),
    ],
)
def test_convert_duration(seconds, expected):
    assert convert_duration(seconds) == expected


def test_convert_duration_accepts_string_number():
    assert convert_duration("125") == "02:05"
