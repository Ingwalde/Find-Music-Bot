from typing import cast

from app.database.db import get_pool
from app.database.repository_modules.common import row_to_dict
from app.utils.types import TrackDict


async def save_track(track: TrackDict) -> int:
    """
    Saves track to database and returns internal track ID.
    Updates cached metadata when the same Deezer track already exists.
    Uses RETURNING id to collapse the insert + id-lookup into one statement.
    """
    async with (await get_pool()).acquire() as conn:
        track_id = await conn.fetchval(
            """
            INSERT INTO tracks (
                deezer_track_id,
                title,
                artist,
                album,
                duration,
                duration_seconds,
                deezer_link,
                cover_url,
                release_date,
                rank,
                popularity
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (deezer_track_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                artist = EXCLUDED.artist,
                album = EXCLUDED.album,
                duration = EXCLUDED.duration,
                duration_seconds = EXCLUDED.duration_seconds,
                deezer_link = EXCLUDED.deezer_link,
                cover_url = EXCLUDED.cover_url,
                release_date = EXCLUDED.release_date,
                rank = EXCLUDED.rank,
                popularity = EXCLUDED.popularity,
                updated_at = NOW()
            RETURNING id
            """,
            str(track.get("deezer_track_id")),
            track.get("title"),
            track.get("artist"),
            track.get("album"),
            track.get("duration"),
            track.get("duration_seconds"),
            track.get("deezer_link"),
            track.get("cover_url"),
            track.get("release_date"),
            track.get("rank"),
            track.get("popularity"),
        )
    return int(track_id)


async def get_tracks_by_artist(
    artist: str,
    exclude_deezer_id: str,
    limit: int = 3,
) -> list[dict]:
    """
    Returns cached tracks by artist from local DB, excluding the given track.
    Ordered by rank descending so the most popular tracks appear first.
    """
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT deezer_track_id, title, artist, album, duration, deezer_link, cover_url
            FROM tracks
            WHERE artist = $1 AND deezer_track_id != $2
            ORDER BY rank DESC
            LIMIT $3
            """,
            artist,
            str(exclude_deezer_id),
            limit,
        )
    return [row_to_dict(row) for row in rows]


async def get_track_by_deezer_id(deezer_track_id: str | int) -> TrackDict | None:
    """
    Returns cached track by Deezer ID from PostgreSQL.
    """
    async with (await get_pool()).acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                deezer_track_id,
                title,
                artist,
                album,
                duration,
                duration_seconds,
                deezer_link,
                cover_url,
                release_date,
                rank,
                popularity,
                spotify_track_id,
                spotify_link,
                spotify_updated_at,
                created_at,
                updated_at
            FROM tracks
            WHERE deezer_track_id = $1
            LIMIT 1
            """,
            str(deezer_track_id),
        )
    if not row:
        return None

    # The SELECT above lists exactly the TrackDict keys, but row_to_dict
    # returns a plain dict — asyncpg cannot carry the shape through. cast
    # documents the boundary instead of widening every caller back to dict.
    return cast(TrackDict, row_to_dict(row))
