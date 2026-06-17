from app.database.db import get_pool


async def get_spotify_data_by_deezer_id(deezer_track_id: str | int) -> dict | None:
    async with (await get_pool()).acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT spotify_track_id, spotify_link, spotify_updated_at
            FROM tracks
            WHERE deezer_track_id = $1
            LIMIT 1
            """,
            str(deezer_track_id),
        )

    if not row:
        return None

    spotify_link = row["spotify_link"]

    if not spotify_link:
        return None

    return {
        "spotify_track_id": row["spotify_track_id"],
        "spotify_link": spotify_link,
        "spotify_updated_at": row["spotify_updated_at"],
    }


async def update_spotify_data_for_track(
    deezer_track_id: str | int,
    spotify_track_id: str,
    spotify_link: str,
) -> None:
    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            UPDATE tracks
            SET
                spotify_track_id = $1,
                spotify_link = $2,
                spotify_updated_at = NOW()
            WHERE deezer_track_id = $3
            """,
            spotify_track_id,
            spotify_link,
            str(deezer_track_id),
        )
