from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Season(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("id", "farmland_id", name="uq_seasons_id_farmland"),
        ForeignKeyConstraint(
            ["crop_variety_id", "crop_id"],
            ["crop_varieties.id", "crop_varieties.crop_id"],
            name="fk_seasons_variety_crop",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled')",
            name="ck_seasons_status",
        ),
        CheckConstraint(
            "actual_harvest_date IS NULL OR planting_date IS NULL "
            "OR actual_harvest_date >= planting_date",
            name="ck_seasons_harvest_after_planting",
        ),
        CheckConstraint(
            "budget_amount IS NULL OR budget_amount >= 0",
            name="ck_seasons_budget_nonnegative",
        ),
        CheckConstraint(
            "actual_yield IS NULL OR actual_yield >= 0",
            name="ck_seasons_yield_nonnegative",
        ),
        Index("ix_seasons_farmland_status", "farmland_id", "status"),
        Index("ix_seasons_crop_id", "crop_id"),
        Index(
            "uq_seasons_one_active_per_farmland",
            "farmland_id",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmlands.id", ondelete="RESTRICT"), nullable=False
    )
    crop_id: Mapped[UUID] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    crop_variety_id: Mapped[UUID | None] = mapped_column()
    variety_name: Mapped[str | None] = mapped_column(String(160))
    planting_date: Mapped[date | None] = mapped_column(Date)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planned")
    current_growth_stage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "growth_stages.id",
            name="fk_seasons_current_growth_stage",
            ondelete="SET NULL",
            use_alter=True,
        )
    )
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    budget_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT"
    )
    actual_yield: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    yield_unit: Mapped[str | None] = mapped_column(String(32))
    outcome_notes: Mapped[str | None] = mapped_column(Text)


class CropRecommendation(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "crop_recommendations"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="ck_crop_recommendations_score_range",
        ),
        CheckConstraint(
            "status IN ('proposed', 'selected', 'dismissed', 'expired')",
            name="ck_crop_recommendations_status",
        ),
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_crop_recommendations_farmland",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_crop_recommendations_farmland_created",
            "farmland_id",
            "created_at",
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    crop_id: Mapped[UUID] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="proposed")
    reasoning: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    knowledge_refs: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )


class SeasonPlan(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "season_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'superseded', 'completed')",
            name="ck_season_plans_status",
        ),
        Index("ix_season_plans_season_status", "season_id", "status"),
    )

    season_id: Mapped[UUID] = mapped_column(
        ForeignKey("seasons.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")


class GrowthStage(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "growth_stages"
    __table_args__ = (
        CheckConstraint("sequence > 0", name="ck_growth_stages_sequence_positive"),
        CheckConstraint(
            "start_day IS NULL OR start_day >= 0",
            name="ck_growth_stages_start_day_nonnegative",
        ),
        CheckConstraint(
            "end_day IS NULL OR start_day IS NULL OR end_day >= start_day",
            name="ck_growth_stages_end_day_after_start",
        ),
        UniqueConstraint(
            "season_plan_id", "sequence", name="uq_growth_stages_plan_sequence"
        ),
        Index("ix_growth_stages_plan_id", "season_plan_id"),
    )

    season_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("season_plans.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    start_day: Mapped[int | None] = mapped_column(Integer)
    end_day: Mapped[int | None] = mapped_column(Integer)
