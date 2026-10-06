from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class FarmerProfile(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "farmer_profiles"
    __table_args__ = (
        UniqueConstraint("farmer_id", name="uq_farmer_profiles_farmer"),
        CheckConstraint(
            "farming_experience_years IS NULL OR farming_experience_years >= 0",
            name="ck_farmer_profiles_experience_nonnegative",
        ),
    )

    farmer_id: Mapped[UUID] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )
    farming_experience_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    equipment: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    livestock: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
