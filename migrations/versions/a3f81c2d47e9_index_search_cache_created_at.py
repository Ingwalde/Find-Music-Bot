"""index search_cache.created_at

Revision ID: a3f81c2d47e9
Revises: cf55a191898c
Create Date: 2026-08-15 07:10:00.000000

search_cache had no active pruning until now — rows were only checked for
staleness on read, so the table grew with every unique query ever searched.
cleanup_expired_search_cache() deletes by `created_at < NOW() - INTERVAL
'24 hours'`, which without this index is a full table scan of exactly the
table that had been allowed to grow unbounded.

Raw SQL via op.execute — no SQLAlchemy ORM/Core models, consistent with the
baseline pattern.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'a3f81c2d47e9'
down_revision: str | None = 'cf55a191898c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_cache_created_at "
        "ON search_cache(created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_search_cache_created_at")
