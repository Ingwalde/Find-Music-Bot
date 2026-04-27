def format_track_card(track: dict) -> str:
    """
    Formats selected track information.
    Deezer link is not displayed here because it is available as an inline button.
    """
    title = track.get("title", "Unknown title")
    artist = track.get("artist", "Unknown artist")
    album = track.get("album", "Unknown album")
    duration = track.get("duration", "00:00")

    return (
        f"🎵 {title}\n\n"
        f"👤 {artist}\n"
        f"💿 {album}\n"
        f"⏱ {duration}"
    )
