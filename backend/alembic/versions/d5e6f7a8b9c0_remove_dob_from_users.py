"""remove dob from users

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-08-12 00:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove DOB if it was created by an earlier local migration attempt."""
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS dob")


def downgrade() -> None:
    """Restore the removed DOB column."""
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS dob DATE")
