from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Conversation(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["farmland_id", "farmer_id"],
            ["farmlands.id", "farmlands.farmer_id"],
            name="fk_conversations_farmland_owner",
            ondelete="RESTRICT",
        ),
        Index("ix_conversations_farmer_created", "farmer_id", "created_at"),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    farmer_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(200))


class ChatMessage(UUIDPrimaryKey, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(
            "sender_type IN ('farmer', 'assistant', 'system')",
            name="ck_chat_messages_sender_type",
        ),
        CheckConstraint(
            "message_type IN ('text', 'image', 'system')",
            name="ck_chat_messages_message_type",
        ),
        CheckConstraint(
            "(message IS NOT NULL AND length(trim(message)) > 0) "
            "OR attachment_key IS NOT NULL",
            name="ck_chat_messages_content_present",
        ),
        Index(
            "ix_chat_messages_conversation_order",
            "conversation_id",
            "created_at",
            "id",
        ),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_type: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(16), nullable=False)
    attachment_key: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
