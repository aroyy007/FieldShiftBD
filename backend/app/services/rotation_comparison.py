"""Deterministic, source-preserving crop-pattern comparisons for Module 2.

This service compares published sequence facts. It does not estimate soil
health, yield, profit, or field-level crop suitability.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.core import Farmland
from app.schemas.m2_rotation import (
    RotationComparisonResponse,
    RotationClimateContext,
    RotationPattern,
    RotationPriority,
    RotationSource,
)


_PATTERNS_PATH = Path(__file__).resolve().parents[1] / "data" / "rotation_patterns.json"
_LAND_TYPE_ALIASES = {
    "high": "high",
    "medium_high": "medium_high",
    "medium low": "medium_low",
    "medium_low": "medium_low",
    "low": "low",
    "very_low": "very_low",
}


@lru_cache(maxsize=1)
def _load_reference() -> dict[str, Any]:
    with _PATTERNS_PATH.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def compare_rotation_patterns(
    farmland: Farmland,
    priorities: list[RotationPriority],
    *,
    previous_crop: str | None = None,
    current_crop: str | None = None,
    current_variety: str | None = None,
    climate_context: dict[str, Any] | None = None,
) -> RotationComparisonResponse:
    """Order published examples by farmer-selected, observable priorities.

    A positive context match requires the active crop and variety to match the
    exact BRRI variety cited by the source plus its recorded land and irrigation
    conditions. Otherwise the result remains explicitly an example only.
    """
    reference = _load_reference()
    applicability = reference["applicability"]
    known_land_types = set(applicability["land_types"])
    raw_land_type = (farmland.land_type or "").strip().casefold()
    land_type = _LAND_TYPE_ALIASES.get(raw_land_type)
    irrigation = farmland.irrigation_available
    fit_notes: list[str] = []
    if not farmland.district and not farmland.upazila:
        fit_notes.append("Farm district/upazila is not recorded; regional applicability cannot be checked.")
    else:
        fit_notes.append("BRRI describes this variety context as generally suitable across Bangladesh; it is not an upazila-level match.")
    if land_type is None:
        fit_notes.append("Farm land type is missing or unrecognized, so land applicability is unknown.")
    elif land_type in known_land_types:
        fit_notes.append(f"Recorded land type ({land_type.replace('_', ' ')}) is included in the BRRI applicability note.")
    else:
        fit_notes.append(f"Recorded land type ({land_type.replace('_', ' ')}) is not listed in the BRRI applicability note.")
    if irrigation is None:
        fit_notes.append("Irrigation availability is not recorded, so the source's irrigated-land context cannot be checked.")
    elif irrigation:
        fit_notes.append("Farm profile records irrigation; BRRI's variety note describes irrigated land.")
    else:
        fit_notes.append("Farm profile records no irrigation, while BRRI's variety note describes irrigated land.")
    fit_notes.append(
        "Soil texture is not used for a match because this BRRI variety page does not specify soil-texture conditions for these patterns."
    )

    current_crop_is_source_crop = bool(current_crop and current_crop.strip().casefold() == "rice")
    current_variety_is_source_variety = bool(
        current_variety and current_variety.strip().casefold() in {"br15", "brri dhan15", "brridhan15"}
    )
    if not current_crop:
        fit_status = "farm_context_incomplete"
        fit_notes.append("No active crop is recorded; these BR15 rice examples cannot be matched to the current crop.")
    elif not current_crop_is_source_crop:
        fit_status = "not_current_source_crop"
        fit_notes.append(f"The source examples are for BR15 rice, while the current crop is {current_crop}.")
    elif not current_variety_is_source_variety:
        fit_status = "source_variety_not_confirmed"
        fit_notes.append("The active crop is rice, but its variety is not confirmed as BR15, the variety cited by this source.")
    elif land_type is None or irrigation is None:
        fit_status = "farm_context_incomplete"
    elif land_type not in known_land_types or not irrigation:
        fit_status = "not_published_conditions"
        fit_notes.append("At least one recorded farm condition does not match the published BR15 context.")
    else:
        fit_status = "matches_published_conditions"

    built: list[RotationPattern] = []
    for item in reference["patterns"]:
        sequence = item["sequence"]
        crop_groups = item["crop_groups"]
        crop_names = [name for name in sequence if name.casefold() != "fallow"]
        fallow_slots = sum(name.casefold() == "fallow" for name in sequence)
        distinct_crop_types = len({group for group in crop_groups if group != "fallow"})
        priority_matches: list[RotationPriority] = []
        if RotationPriority.FEWER_FALLOW_SLOTS in priorities and fallow_slots == 0:
            priority_matches.append(RotationPriority.FEWER_FALLOW_SLOTS)
        if RotationPriority.INCLUDE_LEGUME in priorities and item["contains_legume"]:
            priority_matches.append(RotationPriority.INCLUDE_LEGUME)
        if RotationPriority.MORE_CROP_TYPES in priorities and distinct_crop_types > 1:
            priority_matches.append(RotationPriority.MORE_CROP_TYPES)
        if RotationPriority.MATCH_FARM_CONTEXT in priorities and fit_status == "matches_published_conditions":
            priority_matches.append(RotationPriority.MATCH_FARM_CONTEXT)
        notes = list(item["notes"])
        if previous_crop and crop_names and crop_names[0].casefold() in previous_crop.casefold():
            notes.append("The first sequence crop matches the farmer's recorded previous crop; compare this repeat with local advice.")
        built.append(
            RotationPattern(
                pattern_id=item["id"],
                sequence=sequence,
                crop_slots=len(crop_names),
                distinct_crop_types=distinct_crop_types,
                fallow_slots=fallow_slots,
                contains_legume=item["contains_legume"],
                fit_status=fit_status,
                fit_notes=fit_notes,
                priority_matches=priority_matches,
                sequence_notes=notes,
                source=RotationSource(
                    source_name=reference["source_name"],
                    source_reference=reference["source_reference"],
                    claim=f"Published crop-pattern example associated with {reference['source_crop_variety']}.",
                    limitation="The source pattern and variety context do not prove field-level suitability or a soil-health outcome.",
                ),
            )
        )

    # Show evidence-compatible sequences first, then prioritize only explicit
    # observable facts selected by the farmer. No opaque suitability score.
    fit_order = {
        "matches_published_conditions": 0,
        "farm_context_incomplete": 1,
        "not_published_conditions": 2,
        "source_variety_not_confirmed": 3,
        "not_current_source_crop": 4,
    }
    built.sort(
        key=lambda pattern: (
            fit_order[pattern.fit_status],
            tuple(0 if priority in pattern.priority_matches else 1 for priority in priorities),
            pattern.pattern_id,
        )
    )
    profile_incomplete = (
        not current_crop
        or land_type is None
        or irrigation is None
        or (current_crop_is_source_crop and not current_variety)
    )
    return RotationComparisonResponse(
        farmland_id=farmland.id,
        status=("no_supported_patterns" if not built else "profile_incomplete" if profile_incomplete else "available"),
        priority_order=priorities,
        current_crop=current_crop,
        current_variety=current_variety,
        previous_crop=previous_crop,
        patterns=built[:6],
        additional_evidence=[RotationSource(**item) for item in reference["additional_evidence"]],
        limitations=reference["limitations"],
        climate_context=RotationClimateContext(**(climate_context or {})),
    )
