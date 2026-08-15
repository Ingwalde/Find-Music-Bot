from typing import cast

from app.config.settings import settings
from app.database.db import get_pool
from app.database.repository_modules.common import row_to_dict
from app.database.repository_modules.tracks import save_track
from app.database.repository_modules.users import get_user_id
from app.utils.types import TrackDict


async def add_favorite(telegram_id: int, track: TrackDict) -> None:
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    track_id = await save_track(track)

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO favorites (user_id, track_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            user_id,
            track_id,
        )


async def remove_favorite(telegram_id: int, deezer_track_id: str) -> None:
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            DELETE FROM favorites
            WHERE user_id = $1
            AND track_id = (
                SELECT id FROM tracks
                WHERE deezer_track_id = $2
                LIMIT 1
            )
            """,
            user_id,
            str(deezer_track_id),
        )


async def clear_favorites(telegram_id: int) -> None:
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = $1",
            user_id,
        )


async def is_track_favorite(telegram_id: int, deezer_track_id: str) -> bool:
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return False

    async with (await get_pool()).acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT favorites.id
            FROM favorites
            JOIN tracks ON favorites.track_id = tracks.id
            WHERE favorites.user_id = $1
            AND tracks.deezer_track_id = $2
            LIMIT 1
            """,
            user_id,
            str(deezer_track_id),
        )

    return row is not None


async def get_favorite_tracks(
    telegram_id: int, limit: int | None = None
) -> list[TrackDict]:
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return []

    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                tracks.deezer_track_id,
                tracks.title,
                tracks.artist,
                tracks.album,
                tracks.duration,
                tracks.duration_seconds,
                tracks.deezer_link,
                tracks.cover_url,
                tracks.release_date,
                tracks.rank,
                tracks.popularity,
                tracks.spotify_track_id,
                tracks.spotify_link,
                tracks.spotify_updated_at,
                tracks.created_at,
                tracks.updated_at,
                favorites.created_at AS favorite_created_at
            FROM favorites
            JOIN tracks ON favorites.track_id = tracks.id
            WHERE favorites.user_id = $1
            ORDER BY favorites.created_at DESC
            LIMIT $2
            """,
            user_id,
            settings.FAVORITES_LIMIT if limit is None else limit,
        )

    # Same asyncpg boundary as get_track_by_deezer_id — the SELECT lists the
    # TrackDict columns; row_to_dict cannot preserve that shape.
    return [cast(TrackDict, row_to_dict(row)) for row in rows]
