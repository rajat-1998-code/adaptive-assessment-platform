"""Authentication persistence models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.constants import ROLE_STUDENT
from app.core.database import Base
from app.core.mixins import TimestampMixin


class User(TimestampMixin, Base):
    """Application user that owns sessions and authentication credentials."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("google_oauth_subject", name="uq_users_google_oauth_subject"),
        UniqueConstraint("github_oauth_subject", name="uq_users_github_oauth_subject"),
        Index("ix_users_role", "role"),
        Index("ix_users_is_email_verified", "is_email_verified"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=ROLE_STUDENT)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    google_oauth_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_oauth_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    magic_link_tokens: Mapped[list[MagicLinkToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserSession(TimestampMixin, Base):
    """Tracks an authenticated browser or device session for a user."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("session_identifier", name="uq_user_sessions_session_identifier"),
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index("ix_user_sessions_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_identifier: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, default=uuid.uuid4)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(back_populates="sessions")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="session",
        passive_deletes=True,
    )


class RefreshToken(TimestampMixin, Base):
    """Stored refresh token record used for rotation and revocation."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("token_identifier", name="uq_refresh_tokens_token_identifier"),
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_session_id", "session_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    token_identifier: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
    session: Mapped[UserSession | None] = relationship(back_populates="refresh_tokens")


class MagicLinkToken(TimestampMixin, Base):
    """Single-use magic link token issued for passwordless login."""

    __tablename__ = "magic_link_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_magic_link_tokens_token_hash"),
        Index("ix_magic_link_tokens_user_id", "user_id"),
        Index("ix_magic_link_tokens_expires_at", "expires_at"),
        Index("ix_magic_link_tokens_used_at", "used_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(back_populates="magic_link_tokens")
