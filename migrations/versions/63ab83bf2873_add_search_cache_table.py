"""add search_cache table

Revision ID: 63ab83bf2873
Revises: bf5069cbb1be
Create Date: 2026-06-21 12:15:49.582918

Adds search_cache for the v3.1.2 search result cache. Raw SQL via
op.execute — no SQLAlchemy ORM/Core models, matching the baseline's
pattern. result_json is TEXT, not JSONB: the app never queries inside
the JSON, only stores and retrieves it whole, so JSONB's indexing/query
features would add asyncpg codec complexity with no benefit. The
UNIQUE(query_normalized, source) constraint already creates a backing
index for the lookup key — no separate CREATE INDEX needed.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '63ab83bf2873'
down_revision: str | None = 'bf5069cbb1be'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS search_cache (
            id BIGSERIAL PRIMARY KEY,
            query_normalized TEXT NOT NULL,
            source TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (query_normalized, source)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS search_cache")
