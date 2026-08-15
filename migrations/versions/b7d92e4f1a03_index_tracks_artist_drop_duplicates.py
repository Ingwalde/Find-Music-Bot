"""index tracks(artist, rank) and drop indexes duplicated by UNIQUE

Revision ID: b7d92e4f1a03
Revises: a3f81c2d47e9
Create Date: 2026-08-15 16:20:00.000000

Two independent changes to the same table set.

1. tracks(artist, rank DESC)

   get_tracks_by_artist runs
       WHERE artist = $1 AND deezer_track_id != $2 ORDER BY rank DESC LIMIT $3
   and is reached from get_db_recommendations, which send_track_card calls for
   the "You may also like" block under every track card. The baseline schema
   created eight indexes and none on artist, so the hottest read path in the
   app was a sequential scan plus a sort. The index is composite rather than
   on artist alone so it satisfies the ORDER BY as well as the filter.

2. Dropping idx_users_telegram_id and idx_tracks_deezer_track_id

   users.telegram_id is BIGINT NOT NULL UNIQUE and tracks.deezer_track_id is
   TEXT NOT NULL UNIQUE. PostgreSQL implements each UNIQUE constraint with its
   own backing index (users_telegram_id_key, tracks_deezer_track_id_key), so
   these two hand-made indexes are exact duplicates: they answer no query the
   constraint index cannot, while costing an extra write on every INSERT and
   UPDATE to two of the busiest tables.

   The same reasoning is already recorded in 63ab83bf2873, which deliberately
   did NOT add an index for search_cache's UNIQUE key.

Raw SQL via op.execute — no SQLAlchemy ORM/Core models, consistent with the
baseline pattern.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'b7d92e4f1a03'
down_revision: str | None = 'a3f81c2d47e9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_artist_rank "
        "ON tracks(artist, rank DESC)"
    )
    op.execute("DROP INDEX IF EXISTS idx_users_telegram_id")
    op.execute("DROP INDEX IF EXISTS idx_tracks_deezer_track_id")


def downgrade() -> None:
    # Recreated exactly as the baseline schema declared them, so a downgrade
    # lands on the index set bf5069cbb1be produced.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tracks_deezer_track_id "
        "ON tracks(deezer_track_id)"
    )
    op.execute("DROP INDEX IF EXISTS idx_tracks_artist_rank")
