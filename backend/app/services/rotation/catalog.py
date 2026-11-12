"""Load source-scoped crop-sequence candidates without inventing agronomy."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.contracts.challenge.v1 import FarmProfileSnapshot
from app.services.rotation.calendars import match_calendar_references

DATA_DIR = Path(__file__).resolve().parents[2] / "data/m2_knowledge_sources"
CATALOG_MANIFEST = DATA_DIR / "rotation_catalog_v2.json"


@dataclass(frozen=True)
class CropWindow:
    start: str
    end: str


@dataclass(frozen=True)
class RotationCandidateStep:
    crop_code: str
    season_code: str | None
    event_basis: str
    source_ids: tuple[str, ...]
    window: CropWindow | None = None
    start_date: date | None = None
    end_date: date | None = None
    cultivation_method: str | None = None
    variety_names: tuple[str, ...] = ()
    gdd_target: float | None = None


@dataclass(frozen=True)
class RotationCandidate:
    candidate_id: str
    role: Literal["baseline", "alternative"]
    district_code: str
    steps: tuple[RotationCandidateStep, ...]
    source_ids: tuple[str, ...]
    review_status: str
    applicability: Literal["eligible", "ineligible", "unknown"]
    applicability_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewedRuleSet:
    minimum_turnaround_days: int
    source_ids: tuple[str, ...]
    review_status: Literal["reviewed", "unreviewed"]

    def __post_init__(self) -> None:
        if self.minimum_turnaround_days < 0:
            raise ValueError("Turnaround cannot be negative")


def _key(value: str | None) -> str:
    return re.sub(r"[^\w]", "", (value or "").casefold(), flags=re.UNICODE).replace("_", "")


@lru_cache(maxsize=1)
def _profile_vocabulary() -> dict:
    path = DATA_DIR.parent / "m1_profile_vocabulary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_profile_value(value: str | None, section: str) -> str | None:
    if not value:
        return None
    normalized = _key(value)
    for item in _profile_vocabulary()[section]:
        labels = [item.get("code"), item.get("label_en"), item.get("label_bn"), *item.get("aliases", [])]
        if normalized in {_key(label) for label in labels if label}:
            return item["code"]
    return None


def _read_catalog() -> tuple[dict, dict, dict]:
    manifest = json.loads(CATALOG_MANIFEST.read_text(encoding="utf-8"))
    # Manifest paths are filenames only; prevent a catalog edit from escaping this directory.
    def read_local(name: str) -> dict:
        if Path(name).name != name:
            raise ValueError("Rotation catalog source must be a local filename")
        return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))

    patterns = read_local(manifest["patterns_file"])
    calendars = read_local(manifest["calendar_extensions_file"])
    if (manifest.get("source_review_status") != calendars.get("review_status")
            or manifest.get("activation_allowed") is not False
            or calendars.get("activation_allowed") is not False):
        raise ValueError("Rotation catalog review and activation status are inconsistent")
    return manifest, patterns, calendars


def _history_steps(snapshot: FarmProfileSnapshot) -> tuple[RotationCandidateStep, ...]:
    steps = [RotationCandidateStep(crop_code=item.crop_code, season_code=None,
        event_basis=item.source, source_ids=("farmer-history",), start_date=item.planting_date,
        end_date=item.harvest_date) for item in reversed(snapshot.rotation_history)]
    if snapshot.active_season:
        active = snapshot.active_season
        steps.append(RotationCandidateStep(crop_code=active.crop_code or "unknown", season_code=None,
            event_basis="active_season_expected_harvest", source_ids=("farmer-profile",),
            start_date=active.planting_date, end_date=active.expected_harvest_date))
    if not steps and snapshot.profile.previous_crop:
        # Provisional baseline from the crop the farmer reported at sign-up; undated.
        steps.append(RotationCandidateStep(crop_code=snapshot.profile.previous_crop.strip(), season_code=None,
            event_basis="farmer_reported_previous_crop", source_ids=("farmer-profile",)))
    return tuple(steps[-12:])


def _scope_mismatch(snapshot: FarmProfileSnapshot, patterns: dict) -> tuple[str, ...]:
    profile = snapshot.profile
    scope = patterns["profile_match"]
    reasons = []
    if profile.irrigation_available is False:
        reasons.append("irrigation_available=false conflicts with the cited scope")
    land = _canonical_profile_value(profile.land_type, "land_types")
    allowed_land = {_canonical_profile_value(v, "land_types") or _key(v) for v in scope["land_types"]}
    if land is not None and land not in allowed_land:
        reasons.append("recorded land type is outside the cited scope")
    soil = _canonical_profile_value(profile.soil_type, "soil_textures")
    allowed_soil = {_canonical_profile_value(v, "soil_textures") or _key(v) for v in scope["soil_types"]}
    if soil is not None and soil not in allowed_soil:
        reasons.append("recorded soil type is outside the cited scope")
    return tuple(reasons)


def _pattern_steps(pattern: dict, source_id: str) -> tuple[RotationCandidateStep, ...]:
    result = []
    for item in pattern["steps"]:
        match = match_calendar_references(item)
        exact = match["matching"]
        window = None
        source_ids = [source_id]
        if len(exact) == 1:
            reference = exact[0]
            source_ids.append(reference["source_id"])
            establishment = reference["establishment_window"]
            harvest = reference["harvest_window"]
            # A broad establishment/harvest range is evidence for display, not
            # one exact interval for a deterministic feasibility calculation.
            if (establishment["start"] == establishment["end"]
                    and harvest["start"] == harvest["end"]):
                window = CropWindow(start=establishment["start"], end=harvest["end"])
        result.append(RotationCandidateStep(
            crop_code=item["crop_code"], season_code=item.get("season_code"),
            event_basis="published_sequence_without_reviewed_dates", source_ids=tuple(source_ids),
            window=window, cultivation_method=item.get("cultivation_method"),
            variety_names=tuple(item.get("variety_names", ())), gdd_target=None,
        ))
    return tuple(result)


def load_rotation_candidates(region_code: str, snapshot: FarmProfileSnapshot) -> list[RotationCandidate]:
    """Return the farmer's recorded baseline and cited alternatives for a pilot region.

    A known scope conflict can rule out a published example. Missing profile
    facts and all source-only local applicability remain unknown until review.
    """
    manifest, catalog, _ = _read_catalog()
    code = str(region_code)
    if code not in manifest["supported_regions"]:
        raise ValueError("Choose a supported regional comparison: Rajshahi or Chattogram")
    profile_district = snapshot.profile.district_code
    if profile_district and profile_district != code:
        raise ValueError("Requested region does not match the farm profile district")
    source_id = catalog["source"]["source_id"]
    mismatch = _scope_mismatch(snapshot, catalog)
    baseline = RotationCandidate(
        candidate_id="baseline", role="baseline", district_code=code,
        steps=_history_steps(snapshot), source_ids=("farmer-history",),
        review_status="farmer_recorded", applicability="unknown",
        applicability_reasons=("Recorded history is incomplete evidence, not a validated agronomic plan.",),
    )
    alternatives = []
    for pattern in catalog["patterns"]:
        alternatives.append(RotationCandidate(
            candidate_id=pattern["pattern_id"], role="alternative", district_code=code,
            steps=_pattern_steps(pattern, source_id), source_ids=(source_id,),
            review_status=manifest["source_review_status"],
            applicability="ineligible" if mismatch else "unknown",
            applicability_reasons=mismatch or ("Local applicability and agronomy review are not established.",),
        ))
    return [baseline, *alternatives]
