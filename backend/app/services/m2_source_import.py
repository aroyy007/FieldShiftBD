"""Import policy-accepted M2 evidence into the shared knowledge table."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import AgriculturalKnowledge, Crop
from app.services.m2_source_policy import (
    build_barc_knowledge_record,
    is_valid_automated_acceptance,
)


class M2CropCatalogDependencyError(RuntimeError):
    """The M1-owned crop catalog does not yet contain a required crop."""


class M2SourceImportConflict(RuntimeError):
    """An existing source record is not owned by this automated policy."""


def import_barc_snapshot(
    db: Session, snapshot: Mapping[str, Any], *, evaluated_on: date
) -> tuple[AgriculturalKnowledge, bool]:
    """Import or refresh Potato/Comilla evidence without mutating M1 catalog data."""
    crop = db.scalar(select(Crop).where(func.lower(Crop.name) == "potato"))
    if crop is None:
        raise M2CropCatalogDependencyError(
            "M1 crop catalog must contain Potato before importing M2 evidence"
        )

    proposed = build_barc_knowledge_record(snapshot, crop.id, evaluated_on=evaluated_on)
    existing = db.scalar(select(AgriculturalKnowledge).where(
        AgriculturalKnowledge.crop_id == crop.id,
        AgriculturalKnowledge.category == proposed.category,
        AgriculturalKnowledge.region_code == proposed.region_code,
        AgriculturalKnowledge.source_reference == proposed.source_reference,
    ))
    if existing is None:
        db.add(proposed)
        return proposed, True

    existing_content = existing.content if isinstance(existing.content, dict) else {}
    if not is_valid_automated_acceptance(
        existing, existing_content, crop_name=crop.name
    ):
        raise M2SourceImportConflict(
            "The matching BARC record is not owned by the M2 source policy; it was left unchanged"
        )
    existing.content = proposed.content
    existing.source_name = proposed.source_name
    existing.effective_from = proposed.effective_from
    existing.effective_to = proposed.effective_to
    existing.review_status = proposed.review_status
    existing.reviewed_by = None
    existing.reviewed_at = None
    return existing, False
