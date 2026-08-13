"""add user profile fields

Revision ID: c4d5e6f7a8b9
Revises: 7fbe4f0c2a1d
Create Date: 2026-08-11 23:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "f2a1c3b4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add optional name fields to preserve existing users."""
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Remove the profile fields."""
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
