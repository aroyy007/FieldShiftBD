from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class WeatherEvent(UUIDPrimaryKey, Base):
    __tablename__ = "weather_events"
    __table_args__ = (
        UniqueConstraint("id", "farmland_id", name="uq_weather_events_id_farmland"),
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_weather_events_farmland",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "end_time IS NULL OR end_time >= start_time",
            name="ck_weather_events_end_after_start",
        ),
        Index("ix_weather_events_farmland_start", "farmland_id", "start_time"),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(24))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class WeatherAlert(UUIDPrimaryKey, Base):
    __tablename__ = "weather_alerts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_weather_alerts_farmland",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_weather_alerts_season_farmland",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["weather_event_id", "farmland_id"],
            ["weather_events.id", "weather_events.farmland_id"],
            name="fk_weather_alerts_event_farmland",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "severity IN ('low', 'moderate', 'high', 'critical')",
            name="ck_weather_alerts_severity",
        ),
        CheckConstraint(
            "status IN ('new', 'read', 'actioned', 'dismissed')",
            name="ck_weather_alerts_status",
        ),
        Index(
            "ix_weather_alerts_farmland_status_created",
            "farmland_id",
            "status",
            "created_at",
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID | None] = mapped_column()
    weather_event_id: Mapped[UUID | None] = mapped_column()
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="new")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
