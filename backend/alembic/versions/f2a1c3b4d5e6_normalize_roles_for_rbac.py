"""normalize roles for rbac

Revision ID: f2a1c3b4d5e6
Revises: 7fbe4f0c2a1d
Create Date: 2026-07-28 22:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a1c3b4d5e6"
down_revision: str | Sequence[str] | None = "7fbe4f0c2a1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Some existing development databases were stamped at the authentication
    # migration without actually retaining the users table. Repair that
    # inconsistent state before applying the role normalization.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("is_email_verified", sa.Boolean(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("google_oauth_subject", sa.String(length=255), nullable=True),
            sa.Column("github_oauth_subject", sa.String(length=255), nullable=True),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("google_oauth_subject", name="uq_users_google_oauth_subject"),
            sa.UniqueConstraint("github_oauth_subject", name="uq_users_github_oauth_subject"),
        )
        op.create_index("ix_users_is_email_verified", "users", ["is_email_verified"])
        op.create_index("ix_users_role", "users", ["role"])

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
