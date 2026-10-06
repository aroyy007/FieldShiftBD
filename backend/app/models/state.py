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


class Task(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_tasks_season_farmland",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'skipped', 'cancelled')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name="ck_tasks_priority",
        ),
        CheckConstraint(
            "source IN ('season_plan', 'weather', 'disease', 'farmer', 'system')",
            name="ck_tasks_source",
        ),
        Index("ix_tasks_season_status_due", "season_id", "status", "due_at"),
        Index(
            "uq_tasks_season_source_reference",
            "season_id",
            "source_reference",
            unique=True,
            postgresql_where=text("source_reference IS NOT NULL"),
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID] = mapped_column(nullable=False)
    growth_stage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("growth_stages.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(24), nullable=False, default="normal")
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(200))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Problem(UUIDPrimaryKey, Base):
    __tablename__ = "problems"
    __table_args__ = (
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_problems_farmland",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_problems_season_farmland",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "severity IN ('low', 'moderate', 'high', 'critical')",
            name="ck_problems_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'monitoring', 'resolved', 'dismissed')",
            name="ck_problems_status",
        ),
        Index("ix_problems_farmland_status_created", "farmland_id", "status", "created_at"),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID | None] = mapped_column()
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FarmCheckin(UUIDPrimaryKey, Base):
    __tablename__ = "farm_checkins"
    __table_args__ = (
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_farm_checkins_farmland",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_farm_checkins_season_farmland",
            ondelete="RESTRICT",
        ),
        Index("ix_farm_checkins_farmland_checkin", "farmland_id", "checkin_at"),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID | None] = mapped_column()
    checkin_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    growth_stage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("growth_stages.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    observations: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
