"""add admin_audit table

Revision ID: cf55a191898c
Revises: 63ab83bf2873
Create Date: 2026-08-04 07:36:40.834256

Records every admin action with the acting admin's Telegram ID, the action
name, and an optional JSONB details blob (e.g. rows deleted). Raw SQL via
op.execute — no SQLAlchemy ORM/Core models, consistent with baseline pattern.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'cf55a191898c'
down_revision: str | None = '63ab83bf2873'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit (
            id          BIGSERIAL PRIMARY KEY,
            admin_telegram_id BIGINT NOT NULL,
            action      TEXT NOT NULL,
            details     JSONB,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_audit_admin_telegram_id
        ON admin_audit (admin_telegram_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admin_audit")
