"""Import policy-accepted M2 evidence into the shared knowledge table.

All imports are idempotent: rows use deterministic IDs (or, for the legacy BARC
snapshot, a natural key) and rows owned by people or other policies are never
overwritten; they are reported as conflicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import date
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import AgriculturalKnowledge, Crop, CropVariety
from app.services.m1_reference import crop_definition, geography, normalize_text, normalize_variety_name
from app.services.m2_portal_policy import (
    PortalPolicyError,
    build_bilingual_record,
    build_regional_record,
    build_variety_record,
    claims_manifest,
)
from app.services.m2_source_policy import (
    build_barc_knowledge_record,
    is_valid_automated_acceptance,
)
from app.services.source_captures import SourceCaptureError, capture_manifest, read_verified_json


class M2CropCatalogDependencyError(RuntimeError):
    """The M1-owned crop catalog does not yet contain a required crop."""


class M2SourceImportConflict(RuntimeError):
    """An existing source record is not owned by this automated policy."""


def import_barc_snapshot(
    db: Session, snapshot: Mapping[str, Any], *, evaluated_on: date, crop_id: UUID | None = None
) -> tuple[AgriculturalKnowledge, bool]:
    """Import or refresh Potato/Comilla evidence without mutating M1 catalog data."""
    crop = (
        db.get(Crop, crop_id)
        if crop_id is not None
        else db.scalar(select(Crop).where(func.lower(Crop.name) == "potato"))
    )
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


# ── BARC Agri-Advisory Portal policies ───────────────────────────────────────

@dataclass
class KnowledgeImportReport:
    created: int = 0
    refreshed: int = 0
    unchanged: int = 0
    conflicts: list[str] = dataclass_field(default_factory=list)
    rejected: list[str] = dataclass_field(default_factory=list)
    by_policy: dict[str, int] = dataclass_field(default_factory=dict)


def _comparable(content: Mapping[str, Any]) -> dict[str, Any]:
    """Content without the evaluation date, which changes on every run."""
    copy = {key: value for key, value in content.items() if key != "acceptance_policy"}
    policy = dict(content.get("acceptance_policy") or {})
    policy.pop("evaluated_on", None)
    copy["acceptance_policy"] = policy
    return copy


_ROW_FIELDS = (
    "crop_id", "crop_variety_id", "category", "region_code", "source_name",
    "source_reference", "effective_from", "effective_to",
)


def upsert_policy_row(
    db: Session, proposed: AgriculturalKnowledge, crop_name: str, report: KnowledgeImportReport
) -> None:
    """Insert, refresh, or keep a policy-owned row; never overwrite foreign rows."""
    policy_id = proposed.content["acceptance_policy"]["id"]
    report.by_policy[policy_id] = report.by_policy.get(policy_id, 0) + 1
    existing = db.get(AgriculturalKnowledge, proposed.id)
    if existing is None:
        duplicate = db.scalar(select(AgriculturalKnowledge).where(
            AgriculturalKnowledge.crop_id == proposed.crop_id,
            AgriculturalKnowledge.category == proposed.category,
            AgriculturalKnowledge.region_code == proposed.region_code,
            AgriculturalKnowledge.source_reference == proposed.source_reference,
            AgriculturalKnowledge.crop_variety_id.is_(None)
            if proposed.crop_variety_id is None
            else AgriculturalKnowledge.crop_variety_id == proposed.crop_variety_id,
        ))
        if duplicate is not None:
            report.conflicts.append(
                f"{policy_id}: existing knowledge row {duplicate.id} already covers "
                f"{proposed.source_reference} ({proposed.category}, {proposed.region_code}); left unchanged"
            )
            return
        db.add(proposed)
        db.flush()
        report.created += 1
        return

    existing_content = existing.content if isinstance(existing.content, dict) else {}
    existing_policy = existing_content.get("acceptance_policy") or {}
    if (
        existing.reviewed_by is not None
        or existing.reviewed_at is not None
        or existing_policy.get("id") != policy_id
    ):
        report.conflicts.append(
            f"{policy_id}: row {existing.id} is not owned by this policy (human-reviewed or different policy); left unchanged"
        )
        return
    same = (
        existing.review_status == "approved"
        and _comparable(existing_content) == _comparable(proposed.content)
        and all(getattr(existing, name) == getattr(proposed, name) for name in _ROW_FIELDS)
        and is_valid_automated_acceptance(existing, existing_content, crop_name=crop_name)
    )
    if same:
        report.unchanged += 1
        return
    for name in _ROW_FIELDS:
        setattr(existing, name, getattr(proposed, name))
    existing.content = proposed.content
    existing.review_status = "approved"
    existing.reviewed_by = None
    existing.reviewed_at = None
    db.flush()
    report.refreshed += 1


def _variety_ids_for(db: Session, crop_id: UUID) -> dict[str, UUID]:
    return {
        normalize_text(row.name): row.id
        for row in db.scalars(select(CropVariety).where(CropVariety.crop_id == crop_id))
    }


def import_portal_knowledge(
    db: Session, crop_ids: Mapping[str, UUID], *, evaluated_on: date
) -> KnowledgeImportReport:
    """Build and upsert every BARC portal knowledge record the policies accept."""
    report = KnowledgeImportReport()
    crops = {key: db.get(Crop, crop_id) for key, crop_id in crop_ids.items()}

    for claim in claims_manifest()["claims"]:
        crop = crops.get(claim["crop_key"])
        if crop is None:
            report.rejected.append(f"{claim['claim_id']}: crop {claim['crop_key']} is not in the catalog")
            continue
        try:
            record = build_bilingual_record(claim, crop.id, evaluated_on)
        except (PortalPolicyError, SourceCaptureError) as error:
            report.rejected.append(f"{claim['claim_id']}: {error}")
            continue
        upsert_policy_row(db, record, crop.name, report)

    for crop_key in claims_manifest()["variety_duration"]["crops"]:
        crop = crops.get(crop_key)
        if crop is None:
            report.rejected.append(f"variety durations: crop {crop_key} is not in the catalog")
            continue
        variety_ids = _variety_ids_for(db, crop.id)
        for portal_crop_id in crop_definition(crop_key)["portal_crop_ids"]:
            for item in read_verified_json(f"portal/variety_names_{portal_crop_id}.json"):
                portal_variety_id = int(item["id"])
                variety_id = variety_ids.get(normalize_text(normalize_variety_name(str(item["name"]))))
                if variety_id is None:
                    report.rejected.append(f"{crop_key} variety {item['name']!r}: not in the M1 catalog")
                    continue
                try:
                    record = build_variety_record(crop_key, portal_variety_id, crop.id, variety_id, evaluated_on)
                except (PortalPolicyError, SourceCaptureError) as error:
                    report.rejected.append(f"{crop_key} variety {portal_variety_id}: {error}")
                    continue
                upsert_policy_row(db, record, crop.name, report)

    upazila_codes = sorted(
        path.split("/")[-1].removesuffix(".json")
        for path in capture_manifest()
        if path.startswith("suitability/upazila/")
    )
    for crop_key, crop in crops.items():
        if crop is None:
            continue
        for upazila_code in upazila_codes:
            if upazila_code not in geography().upazilas:
                report.rejected.append(f"regional {crop_key}/{upazila_code}: upazila not in geography")
                continue
            try:
                record = build_regional_record(crop_key, upazila_code, crop.id, evaluated_on)
            except (PortalPolicyError, SourceCaptureError) as error:
                report.rejected.append(f"regional {crop_key}/{upazila_code}: {error}")
                continue
            if record is not None:
                upsert_policy_row(db, record, crop.name, report)
    return report
