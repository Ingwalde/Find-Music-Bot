from datetime import date
from types import SimpleNamespace

import pytest

from app.services.deezer_service import (
    format_deezer_track,
    get_object_value,
    get_popularity_label,
    get_rank,
    get_release_date,
)


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


@pytest.mark.parametrize(
    ("raw_rank", "expected"),
    [
        (None, None),
        ("not-number", None),
        (-1, None),
        (0, None),
        ("123456", 123456),
        (789123, 789123),
    ],
)
def test_get_rank(raw_rank, expected):
    track = SimpleNamespace(rank=raw_rank)

    assert get_rank(track) == expected


def test_get_release_date_from_date_object():
    track = SimpleNamespace(release_date=date(2001, 12, 4))

    assert get_release_date(track) == "2001-12-04"


def test_get_release_date_from_string():
    track = SimpleNamespace(release_date="2001-12-04")

    assert get_release_date(track) == "2001-12-04"


def test_get_object_value_extracts_first_available_attribute():
    obj = SimpleNamespace(name="Nate Dogg", title="Should not be used")

    assert get_object_value(obj, ["name", "title"]) == "Nate Dogg"


def test_get_object_value_returns_default_for_empty_object():
    assert get_object_value(None, ["name"], default="Unknown artist") == "Unknown artist"


def test_format_deezer_track_normalizes_fake_deezer_object():
    artist = SimpleNamespace(name="Nate Dogg")
    album = SimpleNamespace(
        title="Music and Me",
        cover_xl="https://example.com/cover_xl.jpg",
        cover_big="https://example.com/cover_big.jpg",
    )
    track = SimpleNamespace(
        id=671298,
        title="Music & Me",
        artist=artist,
        album=album,
        duration=240,
        link="https://www.deezer.com/track/671298",
        release_date="2001-12-04",
        rank=789123,
    )

    result = format_deezer_track(track)

    assert result == {
        "deezer_track_id": "671298",
        "title": "Music & Me",
        "artist": "Nate Dogg",
        "album": "Music and Me",
        "duration": "04:00",
        "duration_seconds": 240,
        "deezer_link": "https://www.deezer.com/track/671298",
        "cover_url": "https://example.com/cover_xl.jpg",
        "release_date": "2001-12-04",
        "rank": 789123,
        "popularity": "Very high",
    }
