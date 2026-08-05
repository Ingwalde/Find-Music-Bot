from typing import TypedDict


class TrackDict(TypedDict, total=False):
    deezer_track_id: str
    title: str
    artist: str
    album: str
    duration: str
    duration_seconds: int
    deezer_link: str
    cover_url: str | None
    release_date: str | None
    rank: int | None
    popularity: str | None
    spotify_track_id: str
    spotify_link: str
