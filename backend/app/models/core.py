from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Farmer(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "farmers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    # Nullable only for accounts created before password authentication. They
    # must establish a password through an explicit account recovery flow.
    password_hash: Mapped[str | None] = mapped_column(String(255))


class Farmland(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "farmlands"
    __table_args__ = (
        UniqueConstraint("id", "farmer_id", name="uq_farmlands_id_farmer"),
        CheckConstraint("land_area_sqm > 0", name="ck_farmlands_positive_area"),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="ck_farmlands_coordinate_pair",
        ),
        CheckConstraint(
            "land_area_display_unit IN "
            "('square_metre', 'decimal', 'acre', 'hectare')",
            name="ck_farmlands_area_display_unit",
        ),
        CheckConstraint(
            "budget_amount IS NULL OR budget_amount >= 0",
            name="ck_farmlands_budget_nonnegative",
        ),
        CheckConstraint(
            "previous_yield_amount IS NULL OR previous_yield_amount >= 0",
            name="ck_farmlands_yield_nonnegative",
        ),
        CheckConstraint(
            "land_type IS NULL OR land_type IN "
            "('high', 'medium_high', 'medium_low', 'low', 'very_low')",
            name="ck_farmlands_land_type",
        ),
        Index("ix_farmlands_farmer_id", "farmer_id"),
    )

    farmer_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, default="BD", server_default=text("'BD'")
    )
    division: Mapped[str | None] = mapped_column(String(120))
    district: Mapped[str | None] = mapped_column(String(120))
    upazila: Mapped[str | None] = mapped_column(String(120))
    village_or_locality: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    land_area_sqm: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    land_area_display_unit: Mapped[str] = mapped_column(String(24), nullable=False)
    soil_type: Mapped[str | None] = mapped_column(String(120))
    land_type: Mapped[str | None] = mapped_column(String(24))
    irrigation_available: Mapped[bool | None] = mapped_column(Boolean)
    water_source: Mapped[str | None] = mapped_column(String(120))
    equipment: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    farming_method: Mapped[str | None] = mapped_column(String(120))
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    budget_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default=text("'BDT'")
    )
    previous_crop: Mapped[str | None] = mapped_column(String(160))
    previous_yield_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    previous_yield_unit: Mapped[str | None] = mapped_column(String(32))

class Crop(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "crops"

    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    scientific_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)


class FarmlandCropPreference(TimestampMixin, Base):
    __tablename__ = "farmland_crop_preferences"
    __table_args__ = (
        CheckConstraint("preference_rank > 0", name="ck_crop_preference_rank"),
        UniqueConstraint(
            "farmland_id", "preference_rank", name="uq_crop_preference_rank"
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmlands.id", ondelete="CASCADE"), primary_key=True
    )
    crop_id: Mapped[UUID] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), primary_key=True
    )
    preference_rank: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class CropVariety(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "crop_varieties"
    __table_args__ = (
        UniqueConstraint("id", "crop_id", name="uq_crop_varieties_id_crop"),
        UniqueConstraint("crop_id", "name", name="uq_crop_varieties_crop_name"),
    )

    crop_id: Mapped[UUID] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class AgriculturalKnowledge(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "agricultural_knowledge"
    __table_args__ = (
        ForeignKeyConstraint(
            ["crop_variety_id", "crop_id"],
            ["crop_varieties.id", "crop_varieties.crop_id"],
            name="fk_agricultural_knowledge_variety_crop",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'in_review', 'approved', 'rejected')",
            name="ck_agricultural_knowledge_review_status",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL "
            "OR effective_to >= effective_from",
            name="ck_agricultural_knowledge_effective_dates",
        ),
        Index(
            "ix_agricultural_knowledge_crop_status",
            "crop_id",
            "review_status",
        ),
    )

    crop_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT")
    )
    crop_variety_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crop_varieties.id", ondelete="RESTRICT")
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    region_code: Mapped[str | None] = mapped_column(String(80))
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    review_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="draft"
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("farmers.id", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
