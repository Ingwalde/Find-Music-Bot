from app.services.track_formatter import format_track_card


def test_format_track_card_with_full_metadata(sample_track):
    card = format_track_card(sample_track)

    assert "🎵 Music & Me" in card
    assert "👤 Nate Dogg" in card
    assert "💿 Music and Me" in card
    assert "⏱ 04:00" in card
    assert "📅 Release: 2001-12-04" in card
    assert "🔥 Popularity: Very high / Rank: 789123" in card
    assert "https://www.deezer.com" not in card


def test_format_track_card_without_optional_metadata(sample_track):
    track = sample_track.copy()
    track["release_date"] = None
    track["rank"] = None
    track["popularity"] = None

    card = format_track_card(track)

    assert "🎵 Music & Me" in card
    assert "📅 Release:" not in card
    assert "🔥" not in card


def test_format_track_card_with_only_rank(sample_track):
    track = sample_track.copy()
    track["popularity"] = None

    card = format_track_card(track)

    assert "🔥 Rank: 789123" in card
