# backend/app/domain/models.py
"""Domain models for WebLanMasters attention flow."""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base, AsyncAttrs):
    __tablename__ = "roles"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = Column(String(255), nullable=True)
    max_analyses_per_day: Mapped[int] = Column(Integer, default=5)
    users: Mapped[List["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class User(Base, AsyncAttrs):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_role_id", "role_id"),
    )

    id: Mapped[int] = Column(Integer, primary_key=True)
    email: Mapped[str] = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = Column(String(100), nullable=True)
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    gemini_api_key_encrypted: Mapped[Optional[str]] = Column(String(500), nullable=True)
    analyses_today: Mapped[int] = Column(Integer, default=0)
    total_analyses: Mapped[int] = Column(Integer, default=0)
    last_analysis_date: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    role_id: Mapped[Optional[int]] = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), default=1)
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    analyses: Mapped[List["Analysis"]] = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def has_own_api_key(self) -> bool:
        return bool(self.gemini_api_key_encrypted)


class Analysis(Base, AsyncAttrs):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_user_created", "user_id", "created_at"),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)",
            name="ck_quality_score_range",
        ),
    )

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_original: Mapped[str] = Column(Text, nullable=False)
    code_improved: Mapped[Optional[str]] = Column(Text, nullable=True)
    analysis_result: Mapped[str] = Column(Text, nullable=False)
    quality_score: Mapped[Optional[int]] = Column(Integer, nullable=True)
    model_used: Mapped[str] = Column(String(50), default="gemini-2.5-flash", nullable=False)
    tokens_used: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, user_id={self.user_id})>"


class Client(Base, AsyncAttrs):
    __tablename__ = "clients"
    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    email: Mapped[Optional[str]] = Column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = Column(String(50), nullable=True)
    company: Mapped[Optional[str]] = Column(String(100), nullable=True)
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="client")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name={self.name})>"


class Ticket(Base, AsyncAttrs):
    __tablename__ = "tickets"
    id: Mapped[int] = Column(Integer, primary_key=True)
    client_id: Mapped[int] = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = Column(String(20), nullable=False)
    priority: Mapped[int] = Column(Integer, nullable=False, default=3)
    status: Mapped[str] = Column(String(20), nullable=False, default="open")
    summary: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="tickets")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, client_id={self.client_id}, category={self.category})>"


class Conversation(Base, AsyncAttrs):
    __tablename__ = "conversations"
    id: Mapped[int] = Column(Integer, primary_key=True)
    ticket_id: Mapped[int] = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[str] = Column(String(10), nullable=False)
    message: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, ticket_id={self.ticket_id}, sender={self.sender})>"
