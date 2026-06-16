import pytest

from app.services.deezer_service import get_popularity_label


@pytest.mark.parametrize(
    ("rank", "expected"),
    [
        (None, None),
        (0, "Low"),
        (100_000, "Low"),
        (150_000, "Medium"),
        (400_000, "High"),
        (700_000, "Very high"),
        (900_000, "Very high"),
    ],
)
def test_get_popularity_label(rank, expected):
    assert get_popularity_label(rank) == expected
