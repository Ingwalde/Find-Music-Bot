from difflib import SequenceMatcher


def normalize_text(value: str | None) -> str:
    """
    Normalizes text for approximate comparison.
    """
    if not value:
        return ""

    allowed = []

    for char in value.lower():
        if char.isalnum() or char.isspace():
            allowed.append(char)

    return " ".join("".join(allowed).split())


def similarity(left: str | None, right: str | None) -> float:
    """
    Returns similarity score between two strings.
    """
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def build_spotify_queries(title: str, artist: str | None = None) -> list[str]:
    """
    Builds Spotify search queries from strict to broad.
    """
    clean_title = title.strip()
    clean_artist = (artist or "").strip()

    queries = []

    if clean_title and clean_artist:
        queries.append(f'track:"{clean_title}" artist:"{clean_artist}"')
        queries.append(f"{clean_title} {clean_artist}")

    if clean_title:
        queries.append(clean_title)

    return list(dict.fromkeys(query for query in queries if query))


def format_spotify_track(item: dict) -> dict:
    """
    Normalizes Spotify track item into a simple dictionary.
    """
    artists = item.get("artists") or []
    album = item.get("album") or {}
    external_urls = item.get("external_urls") or {}

    artist_names = ", ".join(
        artist.get("name", "Unknown artist")
        for artist in artists
        if artist.get("name")
    )

    return {
        "spotify_track_id": item.get("id"),
        "spotify_title": item.get("name"),
        "spotify_artist": artist_names,
        "spotify_album": album.get("name"),
        "spotify_link": external_urls.get("spotify"),
    }


def score_spotify_candidate(
    candidate: dict,
    title: str,
    artist: str | None,
) -> float:
    """
    Scores Spotify search result against Deezer track metadata.
    """
    title_score = similarity(candidate.get("spotify_title"), title)
    artist_score = similarity(candidate.get("spotify_artist"), artist or "")

    if artist:
        return (title_score * 0.7) + (artist_score * 0.3)

    return title_score
