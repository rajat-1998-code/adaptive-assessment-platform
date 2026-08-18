"""add documents table and migrate legacy upload metadata

Revision ID: a1b2c3d4e5f6
Revises: e6f7a8b9c0d1, f2a1c3b4d5e6
Create Date: 2026-08-15 21:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = ("e6f7a8b9c0d1", "f2a1c3b4d5e6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create documents and migrate any legacy uploads table."""

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_guest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.String(length=1024), nullable=True),
        sa.Column(
            "processing_status",
            sa.String(length=32),
            server_default=sa.text("'uploaded'"),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "(owner_user_id IS NOT NULL) != (owner_guest_id IS NOT NULL)",
            name="ck_documents_single_owner",
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, column in (
        ("ix_documents_owner_user_id", "owner_user_id"),
        ("ix_documents_owner_guest_id", "owner_guest_id"),
        ("ix_documents_title", "title"),
        ("ix_documents_original_filename", "original_filename"),
        ("ix_documents_processing_status", "processing_status"),
        ("ix_documents_created_at", "created_at"),
    ):
        op.create_index(name, "documents", [column], unique=False)

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("uploads"):
        op.execute(
            sa.text(
                """
                INSERT INTO documents (
                    id, owner_user_id, owner_guest_id, title, original_filename,
                    content_type, file_size, storage_key, processing_status,
                    created_at, updated_at
                )
                SELECT id, owner_user_id, owner_guest_id,
                       regexp_replace(filename, '\\.[^.]*$', ''), filename,
                       content_type, size_bytes, NULL, 'uploaded',
                       created_at, updated_at
                FROM uploads
                """
            )
        )
        op.drop_table("uploads")


def downgrade() -> None:
    """Drop the document table; migrated legacy rows are not recreated."""

    for name in (
        "ix_documents_created_at",
        "ix_documents_processing_status",
        "ix_documents_original_filename",
        "ix_documents_title",
        "ix_documents_owner_guest_id",
        "ix_documents_owner_user_id",
    ):
        op.drop_index(name, table_name="documents")
    op.drop_table("documents")
