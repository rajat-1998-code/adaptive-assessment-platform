"""normalize roles for rbac

Revision ID: f2a1c3b4d5e6
Revises: 7fbe4f0c2a1d
Create Date: 2026-07-28 22:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a1c3b4d5e6"
down_revision: str | Sequence[str] | None = "7fbe4f0c2a1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        sa.text(
            """
            UPDATE users
            SET role = CASE
                WHEN role IN ('instructor', 'reviewer') THEN 'professional'
                WHEN role IS NULL OR btrim(role) = '' THEN 'student'
                ELSE lower(role)
            END
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        sa.text(
            """
            UPDATE users
            SET role = CASE
                WHEN role = 'professional' THEN 'instructor'
                ELSE role
            END
            """
        )
    )
