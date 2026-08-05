from app.utils.types import TrackDict


def format_track_card(track: TrackDict) -> str:
    """
    Formats selected track information.
    Deezer link is not displayed here because it is available as an inline button.
    """
    title = track.get("title", "Unknown title")
    artist = track.get("artist", "Unknown artist")
    album = track.get("album", "Unknown album")
    duration = track.get("duration", "00:00")
    release_date = track.get("release_date")
    rank = track.get("rank")
    popularity = track.get("popularity")

    lines = [
        f"🎵 {title}",
        "",
        f"👤 {artist}",
        f"💿 {album}",
        f"⏱ {duration}",
    ]

    if release_date:
        lines.append(f"📅 Release: {release_date}")

    if popularity and rank:
        lines.append(f"🔥 Popularity: {popularity} / Rank: {rank}")
    elif popularity:
        lines.append(f"🔥 Popularity: {popularity}")
    elif rank:
        lines.append(f"🔥 Rank: {rank}")

    return "\n".join(lines)
