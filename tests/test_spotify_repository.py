from app.database import repositories as repo
from app.database.repository_modules.spotify import (
    get_spotify_data_by_deezer_id,
    update_spotify_data_for_track,
)


def test_get_spotify_data_returns_none_for_missing_track(temp_database):
    assert get_spotify_data_by_deezer_id("missing") is None


def test_get_spotify_data_returns_none_without_spotify_link(temp_database, sample_track):
    repo.save_track(sample_track)

    assert get_spotify_data_by_deezer_id(sample_track["deezer_track_id"]) is None


def test_update_and_read_spotify_data(temp_database, sample_track):
    repo.save_track(sample_track)

    update_spotify_data_for_track(
        deezer_track_id=sample_track["deezer_track_id"],
        spotify_track_id="spotify123",
        spotify_link="https://open.spotify.com/track/spotify123",
    )

    spotify_data = get_spotify_data_by_deezer_id(sample_track["deezer_track_id"])

    assert spotify_data["spotify_track_id"] == "spotify123"
    assert spotify_data["spotify_link"] == "https://open.spotify.com/track/spotify123"
    assert spotify_data["spotify_updated_at"] is not None
