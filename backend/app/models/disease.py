from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class DiseaseResult(UUIDPrimaryKey, Base):
    __tablename__ = "disease_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["farmland_id"],
            ["farmlands.id"],
            name="fk_disease_results_farmland",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["season_id", "farmland_id"],
            ["seasons.id", "seasons.farmland_id"],
            name="fk_disease_results_season_farmland",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_disease_results_confidence_range",
        ),
        Index(
            "ix_disease_results_farmland_created",
            "farmland_id",
            "created_at",
        ),
    )

    farmland_id: Mapped[UUID] = mapped_column(nullable=False)
    season_id: Mapped[UUID | None] = mapped_column()
    crop_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT")
    )
    image_storage_key: Mapped[str | None] = mapped_column(Text)
    possible_issue: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    symptoms: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    recommended_actions: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    model_details: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
