"""
Property-based tests for pure/deterministic functions (v3.4.2).

Invariants tested:
- convert_duration: output always contains ":", correct colon count, 2-digit
  segments, and exact round-trip fidelity.
- normalize_query: idempotent, always lowercase, always stripped.
- get_popularity_label: correct label for every rank range, None passthrough.
- format_track_card: always contains the supplied title/artist/album strings.
- truncate_text: result never exceeds max_length; no-ops for short inputs.
- split_long_message: every chunk fits; reassembled output equals original.
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.deezer_service import get_popularity_label
from app.services.search_cache_service import normalize_query
from app.services.track_formatter import format_track_card
from app.utils.text import split_long_message, truncate_text
from app.utils.time import convert_duration

# ---------------------------------------------------------------------------
# convert_duration
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=359_999))
def test_convert_duration_always_has_colon(seconds):
    assert ":" in convert_duration(seconds)


@given(st.integers(min_value=0, max_value=3_599))
def test_convert_duration_under_one_hour_has_one_colon(seconds):
    assert convert_duration(seconds).count(":") == 1


@given(st.integers(min_value=3_600, max_value=359_999))
def test_convert_duration_one_hour_or_more_has_two_colons(seconds):
    assert convert_duration(seconds).count(":") == 2


@given(st.integers(min_value=0, max_value=359_999))
def test_convert_duration_every_segment_is_two_digits(seconds):
    for part in convert_duration(seconds).split(":"):
        assert len(part) == 2 and part.isdigit()


@given(st.integers(min_value=0, max_value=359_999))
def test_convert_duration_round_trip(seconds):
    parts = [int(p) for p in convert_duration(seconds).split(":")]
    if len(parts) == 3:
        reconstructed = parts[0] * 3600 + parts[1] * 60 + parts[2]
    else:
        reconstructed = parts[0] * 60 + parts[1]
    assert reconstructed == seconds


# ---------------------------------------------------------------------------
# normalize_query
# ---------------------------------------------------------------------------


@given(st.text())
def test_normalize_query_is_idempotent(query):
    assert normalize_query(normalize_query(query)) == normalize_query(query)


@given(st.text())
def test_normalize_query_result_is_lowercase(query):
    result = normalize_query(query)
    assert result == result.lower()


@given(st.text())
def test_normalize_query_result_is_stripped(query):
    result = normalize_query(query)
    assert result == result.strip()


# ---------------------------------------------------------------------------
# get_popularity_label
# ---------------------------------------------------------------------------


def test_get_popularity_label_none_returns_none():
    assert get_popularity_label(None) is None


@given(st.integers(min_value=700_000, max_value=1_000_000))
def test_get_popularity_label_high_rank_is_very_high(rank):
    assert get_popularity_label(rank) == "Very high"


@given(st.integers(min_value=400_000, max_value=699_999))
def test_get_popularity_label_mid_high_rank_is_high(rank):
    assert get_popularity_label(rank) == "High"


@given(st.integers(min_value=150_000, max_value=399_999))
def test_get_popularity_label_mid_rank_is_medium(rank):
    assert get_popularity_label(rank) == "Medium"


@given(st.integers(min_value=0, max_value=149_999))
def test_get_popularity_label_low_rank_is_low(rank):
    assert get_popularity_label(rank) == "Low"


# ---------------------------------------------------------------------------
# format_track_card
# ---------------------------------------------------------------------------

_field_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cc",)),
    min_size=1,
    max_size=80,
)


@given(title=_field_text, artist=_field_text, album=_field_text)
def test_format_track_card_contains_title_artist_album(title, artist, album):
    result = format_track_card({"title": title, "artist": artist, "album": album})
    assert title in result
    assert artist in result
    assert album in result


@given(title=_field_text, artist=_field_text, album=_field_text)
def test_format_track_card_result_is_nonempty(title, artist, album):
    result = format_track_card({"title": title, "artist": artist, "album": album})
    assert len(result) > 0


def test_format_track_card_empty_dict_uses_fallbacks():
    result = format_track_card({})
    assert "Unknown title" in result
    assert "Unknown artist" in result
    assert "Unknown album" in result


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------


@given(
    text=st.text(max_size=200),
    # Was min_value=4, which started just above the range where the negative
    # slice made the result LONGER than max_length — the bound had been fitted
    # to the bug rather than to any real precondition.
    max_length=st.integers(min_value=0, max_value=128),
)
def test_truncate_text_never_exceeds_max_length(text, max_length):
    assert len(truncate_text(text, max_length)) <= max_length


@given(text=st.text(min_size=1, max_size=200))
def test_truncate_text_to_zero_is_empty(text):
    assert truncate_text(text, 0) == ""


@given(
    text=st.text(min_size=10, max_size=200),
    max_length=st.integers(min_value=1, max_value=3),
)
def test_truncate_text_below_ellipsis_width_drops_the_marker(text, max_length):
    """No room for '...' means a plain cut, not an over-length string."""
    result = truncate_text(text, max_length)

    assert len(result) == max_length
    assert "..." not in result


@given(
    text=st.text(max_size=128),
    max_length=st.integers(min_value=4, max_value=128),
)
def test_truncate_text_short_input_is_unchanged(text, max_length):
    if len(text) <= max_length:
        assert truncate_text(text, max_length) == text


# ---------------------------------------------------------------------------
# split_long_message
# ---------------------------------------------------------------------------


@given(
    text=st.text(max_size=8_000),
    max_length=st.integers(min_value=10, max_value=500),
)
@settings(max_examples=200)
def test_split_long_message_all_chunks_fit(text, max_length):
    for chunk in split_long_message(text, max_length):
        assert len(chunk) <= max_length


@given(
    text=st.text(max_size=8_000),
    max_length=st.integers(min_value=10, max_value=500),
)
@settings(max_examples=200)
def test_split_long_message_reassembled_equals_original(text, max_length):
    assert "".join(split_long_message(text, max_length)) == text


@given(st.text(min_size=1, max_size=8_000))
def test_split_long_message_nonempty_text_produces_at_least_one_chunk(text):
    assert len(split_long_message(text)) >= 1
