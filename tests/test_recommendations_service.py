import pytest

from app.services import recommendations_service
from app.services.recommendations_service import (
    _get_decade,
    format_recommendations_text,
    format_similar_text,
    get_cached_trending,
    get_db_recommendations,
    get_similar_by_genre,
    invalidate_trending_cache,
)
from tests.conftest import to_async


def make_track(title="SOS", artist="ABBA", link="https://deezer.com/track/1"):
    return {
        "deezer_track_id": "1",
        "title": title,
        "artist": artist,
        "album": "Gold",
        "duration": "03:30",
        "deezer_link": link,
    }


@pytest.mark.asyncio
async def test_get_cached_trending_calls_fetch_fn_on_empty_cache():
    invalidate_trending_cache()
    calls = []

    async def fetch(limit):
        calls.append(limit)
        return [make_track()]

    result = await get_cached_trending(fetch, limit=5)

    assert len(calls) == 1
    assert calls[0] == 5
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_cached_trending_returns_cached_on_second_call():
    invalidate_trending_cache()
    call_count = []

    async def fetch(limit):
        call_count.append(1)
        return [make_track()]

    await get_cached_trending(fetch)
    await get_cached_trending(fetch)

    assert len(call_count) == 1


@pytest.mark.asyncio
async def test_invalidate_trending_cache_forces_refetch():
    invalidate_trending_cache()
    call_count = []

    async def fetch(limit):
        call_count.append(1)
        return [make_track()]

    await get_cached_trending(fetch)
    invalidate_trending_cache()
    await get_cached_trending(fetch)

    assert len(call_count) == 2


@pytest.mark.asyncio
async def test_get_cached_trending_does_not_cache_empty_result():
    invalidate_trending_cache()
    call_count = []

    async def fetch(limit):
        call_count.append(1)
        return []

    await get_cached_trending(fetch)
    await get_cached_trending(fetch)

    assert len(call_count) == 2


@pytest.mark.asyncio
async def test_get_db_recommendations_returns_db_tracks_when_available(monkeypatch):
    tracks = [make_track("Waterloo", "ABBA")]
    monkeypatch.setattr(recommendations_service, "get_tracks_by_artist", to_async(lambda **kwargs: tracks))

    result = await get_db_recommendations(artist="ABBA", exclude_deezer_id="99")

    assert result == tracks


@pytest.mark.asyncio
async def test_get_db_recommendations_falls_back_to_deezer_when_db_empty(monkeypatch):
    fallback = [make_track("Gimme", "ABBA")]
    monkeypatch.setattr(recommendations_service, "get_tracks_by_artist", to_async(lambda **kwargs: []))
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda **kwargs: fallback))

    result = await get_db_recommendations(artist="ABBA", exclude_deezer_id="99")

    assert result == fallback


@pytest.mark.asyncio
async def test_get_db_recommendations_returns_empty_when_both_empty(monkeypatch):
    monkeypatch.setattr(recommendations_service, "get_tracks_by_artist", to_async(lambda **kwargs: []))
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda **kwargs: []))

    result = await get_db_recommendations(artist="Unknown", exclude_deezer_id="0")

    assert result == []


def test_format_recommendations_text_returns_empty_for_empty_list():
    assert format_recommendations_text([]) == ""


def test_format_recommendations_text_includes_track_info():
    tracks = [make_track("SOS", "ABBA", "https://deezer.com/1")]
    text = format_recommendations_text(tracks)

    assert "ABBA" in text
    assert "SOS" in text
    assert "https://deezer.com/1" in text


def test_format_recommendations_text_omits_link_when_missing():
    tracks = [{"title": "SOS", "artist": "ABBA", "deezer_link": ""}]
    text = format_recommendations_text(tracks)

    assert "ABBA — SOS" in text
    assert "http" not in text


def test_format_recommendations_text_numbers_multiple_tracks():
    tracks = [
        make_track("SOS", "ABBA"),
        make_track("Waterloo", "ABBA"),
    ]
    text = format_recommendations_text(tracks)

    assert "1." in text
    assert "2." in text


def test_format_recommendations_text_grouped_same_artist_only():
    tracks = [
        make_track("SOS", "ABBA", "https://deezer.com/1"),
        make_track("Waterloo", "ABBA", "https://deezer.com/2"),
    ]
    text = format_recommendations_text(tracks, source_artist="ABBA")

    assert "🎤 ABBA" in text
    assert "- [SOS]" in text
    assert "- [Waterloo]" in text
    assert "🎵 Others" not in text
    assert "ABBA —" not in text


def test_format_recommendations_text_grouped_others_only():
    tracks = [make_track("Rivers Of Babylon", "Boney M", "https://deezer.com/3")]
    text = format_recommendations_text(tracks, source_artist="ABBA")

    assert "🎵 Others" in text
    assert "Rivers Of Babylon" in text
    assert "Boney M" in text
    assert "🎤 ABBA" not in text


def test_format_recommendations_text_grouped_mixed():
    tracks = [
        make_track("SOS", "ABBA", "https://deezer.com/1"),
        make_track("Rivers Of Babylon", "Boney M", "https://deezer.com/3"),
    ]
    text = format_recommendations_text(tracks, source_artist="ABBA")

    assert "🎤 ABBA" in text
    assert "🎵 Others" in text
    assert "- [SOS]" in text
    assert "Rivers Of Babylon" in text
    assert "Boney M" in text


def test_format_recommendations_text_grouped_no_link_in_same_artist():
    tracks = [{"title": "SOS", "artist": "ABBA", "deezer_link": ""}]
    text = format_recommendations_text(tracks, source_artist="ABBA")

    assert "- SOS" in text
    assert "http" not in text


def test_format_recommendations_text_grouped_no_link_in_others():
    tracks = [{"title": "Rivers Of Babylon", "artist": "Boney M", "deezer_link": ""}]
    text = format_recommendations_text(tracks, source_artist="ABBA")

    assert "- Rivers Of Babylon — Boney M" in text
    assert "http" not in text


def test_format_similar_text_returns_header_when_no_tracks():
    text = format_similar_text("🎯 Similar to SOS — ABBA", [], "ABBA")

    assert text == "🎯 Similar to SOS — ABBA"


def test_format_similar_text_grouped_by_source_artist():
    tracks = [
        make_track("Waterloo", "ABBA", "https://deezer.com/2"),
        make_track("Rivers Of Babylon", "Boney M", "https://deezer.com/3"),
    ]
    text = format_similar_text("🎯 Header", tracks, source_artist="ABBA")

    assert text.startswith("🎯 Header\n\n")
    assert "🎤 ABBA" in text
    assert "🎵 Others" in text
    assert "- [Waterloo]" in text
    assert "Rivers Of Babylon" in text


def test_format_similar_text_fallback_numbered_list_when_no_source_artist():
    tracks = [
        make_track("SOS", "ABBA", "https://deezer.com/1"),
        make_track("Waterloo", "ABBA", "https://deezer.com/2"),
    ]
    text = format_similar_text("🎯 Header", tracks, source_artist="")

    assert text.startswith("🎯 Header\n\n")
    assert "1." in text
    assert "2." in text


def make_similar_track(track_id="2", title="Waterloo", artist="ABBA", rank=500000):
    return {
        "deezer_track_id": track_id,
        "title": title,
        "artist": artist,
        "deezer_link": f"https://deezer.com/track/{track_id}",
        "rank": rank,
    }


@pytest.mark.asyncio
async def test_get_similar_by_genre_step1_returns_artist_tracks(monkeypatch):
    tracks = [make_similar_track(track_id=str(i)) for i in range(2, 7)]
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: tracks))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: None))

    result = await get_similar_by_genre("1", artist_name="ABBA")

    assert len(result) == 5
    assert all(t["deezer_track_id"] != "1" for t in result)


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_fills_with_related_tracks(monkeypatch):
    artist_tracks = [make_similar_track(track_id="2"), make_similar_track(track_id="3")]
    related_tracks = [make_similar_track(track_id=str(i), rank=500000) for i in range(10, 20)]
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: artist_tracks)
    )
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: None))
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: related_tracks)
    )

    result = await get_similar_by_genre("1", artist_name="ABBA", limit=10)

    assert len(result) == 10
    assert result[0]["deezer_track_id"] == "2"


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_dedupes_related_tracks(monkeypatch):
    artist_track = make_similar_track(track_id="2")
    related_returns = [
        make_similar_track(track_id="2"),
        make_similar_track(track_id="3", title="Fernando"),
    ]
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: [artist_track])
    )
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: None))
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: related_returns)
    )

    result = await get_similar_by_genre("1", artist_name="ABBA")

    ids = [t["deezer_track_id"] for t in result]
    assert ids.count("2") == 1
    assert "3" in ids


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_rank_filter_excludes_out_of_range(monkeypatch):
    in_range = make_similar_track(track_id="2", rank=600000)
    out_of_range = make_similar_track(track_id="3", rank=100)
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": 500000}))
    monkeypatch.setattr(
        recommendations_service,
        "get_artist_top_tracks_by_id",
        to_async(lambda aid, limit=10: [in_range, out_of_range]),
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1
    assert result[0]["rank"] == 600000


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_null_rank_track_included(monkeypatch):
    null_rank = make_similar_track(track_id="2", rank=None)
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": 500000}))
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: [null_rank])
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1
    assert result[0]["rank"] is None


@pytest.mark.asyncio
async def test_get_similar_by_genre_step3_fallback_when_both_empty(monkeypatch):
    fallback_track = make_similar_track(track_id="99", title="Fallback")
    call_count = [0]

    async def mock_artist_top(artist_name, limit):
        call_count[0] += 1
        if call_count[0] == 1:
            return []
        return [fallback_track]

    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", mock_artist_top)
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: None))

    result = await get_similar_by_genre("1", artist_name="ABBA")

    assert result == [fallback_track]
    assert call_count[0] == 2


def test_get_decade_returns_correct_decade_for_valid_date():
    assert _get_decade("1976-01-01") == (1970, 1979)
    assert _get_decade("1980-06-15") == (1980, 1989)
    assert _get_decade("2000-12-31") == (2000, 2009)
    assert _get_decade("1900-01-01") == (1900, 1909)


def test_get_decade_returns_none_for_invalid_or_out_of_range():
    assert _get_decade(None) is None
    assert _get_decade("") is None
    assert _get_decade("0000-00-00") is None
    assert _get_decade("2200-01-01") is None
    assert _get_decade("not-a-date") is None


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_decade_filter_includes_same_decade(monkeypatch):
    track_in_decade = {**make_similar_track(track_id="2"), "release_date": "1975-06-01"}
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": "1976-01-01"})
    )
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: [track_in_decade])
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_pass_b_includes_different_decade_when_pass_a_insufficient(monkeypatch):
    track_wrong_decade = {**make_similar_track(track_id="2"), "release_date": "1985-01-01"}
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": "1976-01-01"})
    )
    monkeypatch.setattr(
        recommendations_service,
        "get_artist_top_tracks_by_id",
        to_async(lambda aid, limit=10: [track_wrong_decade]),
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_null_date_track_included_when_decade_known(monkeypatch):
    no_date_track = make_similar_track(track_id="2")
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": "1976-01-01"})
    )
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: [no_date_track])
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_pass_b_skipped_when_pass_a_sufficient(monkeypatch):
    same_decade = [
        {**make_similar_track(track_id=str(i)), "release_date": "1975-01-01"}
        for i in range(2, 7)
    ]
    wrong_decade = {**make_similar_track(track_id="99"), "release_date": "1985-01-01"}
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": "1976-01-01"})
    )
    monkeypatch.setattr(
        recommendations_service,
        "get_artist_top_tracks_by_id",
        to_async(lambda aid, limit=10: same_decade + [wrong_decade]),
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 5
    assert all(t["release_date"] == "1975-01-01" for t in result)
    assert "99" not in [t["deezer_track_id"] for t in result]


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_pass_b_fills_when_pass_a_insufficient(monkeypatch):
    wrong_decade = [
        {**make_similar_track(track_id=str(i)), "release_date": "1985-01-01"}
        for i in range(2, 5)
    ]
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": "1976-01-01"})
    )
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: wrong_decade)
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_similar_by_genre_step2_no_decade_filter_when_source_date_unknown(monkeypatch):
    track_1985 = {**make_similar_track(track_id="2"), "release_date": "1985-01-01"}
    monkeypatch.setattr(recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: []))
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(
        recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: {"rank": None, "release_date": None})
    )
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: [track_1985])
    )

    result = await get_similar_by_genre("1")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_similar_by_genre_respects_limit(monkeypatch):
    artist_tracks = [make_similar_track(track_id=str(i)) for i in range(2, 5)]
    related_tracks = [make_similar_track(track_id=str(i), rank=500000) for i in range(10, 20)]
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks", to_async(lambda artist_name, limit: artist_tracks)
    )
    monkeypatch.setattr(recommendations_service, "get_artist_id", to_async(lambda name: 7))
    monkeypatch.setattr(
        recommendations_service,
        "get_related_artists",
        to_async(lambda aid, limit=3: [{"id": 8, "name": "Queen"}]),
    )
    monkeypatch.setattr(recommendations_service, "get_track_by_deezer_id", to_async(lambda tid: None))
    monkeypatch.setattr(
        recommendations_service, "get_artist_top_tracks_by_id", to_async(lambda aid, limit=10: related_tracks)
    )

    result = await get_similar_by_genre("1", artist_name="ABBA", limit=5)

    assert len(result) == 5
