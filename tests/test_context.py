from app.bot.context import (
    get_current_page,
    get_page_tracks,
    get_search_context,
    get_total_pages,
    save_search_context,
    set_search_page,
)


def make_tracks(count: int) -> list[dict]:
    return [{"deezer_track_id": str(index), "title": f"Track {index}"} for index in range(count)]


def test_save_and_get_search_context():
    tracks = make_tracks(3)

    save_search_context(user_id=1, query="test", tracks=tracks)

    context = get_search_context(1)

    assert context["query"] == "test"
    assert context["tracks"] == tracks
    assert context["page"] == 0


def test_get_total_pages():
    save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    assert get_total_pages(user_id=1, page_size=5) == 3


def test_get_page_tracks_returns_expected_slice():
    save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    page_zero = get_page_tracks(user_id=1, page_size=5, page=0)
    page_two = get_page_tracks(user_id=1, page_size=5, page=2)

    assert [track["title"] for track in page_zero] == [
        "Track 0",
        "Track 1",
        "Track 2",
        "Track 3",
        "Track 4",
    ]
    assert [track["title"] for track in page_two] == ["Track 10", "Track 11"]


def test_set_search_page_normalizes_low_and_high_values():
    save_search_context(user_id=1, query="test", tracks=make_tracks(12))

    assert set_search_page(user_id=1, page=-10, page_size=5) == 0
    assert get_current_page(1) == 0

    assert set_search_page(user_id=1, page=999, page_size=5) == 2
    assert get_current_page(1) == 2


def test_missing_context_returns_safe_defaults():
    assert get_search_context(999) is None
    assert get_total_pages(user_id=999, page_size=5) == 0
    assert get_page_tracks(user_id=999, page_size=5) == []
    assert get_current_page(999) == 0
