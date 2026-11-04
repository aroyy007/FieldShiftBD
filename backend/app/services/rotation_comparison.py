"""Evidence-bounded comparison of published Bangladesh crop sequences.

This provider is read-only. It presents source patterns only when the saved
farm profile matches their stated land, soil, and irrigation scope; it does not
rank rotations or create operational seasons.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from app.contracts.challenge.v1 import (
    CONTRACT_VERSION,
    FarmProfileSnapshot,
    RotationComparison,
    RotationSequenceStep,
    RotationStepCalendarEvidence,
    RotationStrategy,
    RotationTradeoff,
    SourceProvenance,
)
from app.contracts.challenge.ports import ArtifactNotFound, AdapterConflict, StaleArtifact
from app.services.climate.cache import CorruptClimateCache
from app.services.crop_calendar_references import calendar_reference_for_variety
from app.services.district_advisory import load_district_climate_evidence


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "m2_knowledge_sources"
    / "brri_rotation_patterns.json"
)
DISPLAYED_PATTERN_IDS = {"BRRI-RFS-02", "BRRI-RFS-04"}


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split()) or None


class BrriRotationComparisonProvider:
    """Compare a farm's recorded crop sequence with applicable BRRI patterns."""

    def __init__(self, catalog_path: Path = CATALOG_PATH, *, climate_cache_root: Path | None = None) -> None:
        self._catalog_path = catalog_path
        self._climate_cache_root = climate_cache_root

    def compare(
        self,
        snapshot: FarmProfileSnapshot,
        *,
        now: datetime | None = None,
    ) -> RotationComparison:
        created_at = now or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        catalog = json.loads(self._catalog_path.read_text(encoding="utf-8"))
        evidence = [self._provenance(catalog)]
        current_sequence, current_sequence_basis = self._current_sequence(snapshot)
        unknowns_en, unknowns_bn, scope_notes_en, scope_notes_bn, outside_scope = (
            self._profile_gaps(snapshot, catalog)
        )

        alternatives: list[list[str]] = []
        strategies: list[RotationStrategy] = []
        if not unknowns_en and not outside_scope:
            for pattern in catalog["patterns"]:
                if pattern["pattern_id"] not in DISPLAYED_PATTERN_IDS:
                    continue
                steps = [RotationSequenceStep.model_validate(step) for step in pattern["steps"]]
                alternatives.append([step.crop_code for step in steps])
                strategies.append(self._strategy(pattern, steps, catalog))

        climate_evidence = None
        climate_status = "not_configured"
        if self._climate_cache_root is not None:
            climate_status = "unavailable"
            district = snapshot.profile.district_code or snapshot.profile.district
            if district:
                try:
                    climate_evidence = load_district_climate_evidence(self._climate_cache_root, district)
                    climate_status = climate_evidence.status
                except (ArtifactNotFound, AdapterConflict, StaleArtifact, CorruptClimateCache, OSError, ValueError):
                    scope_notes_en.append("District NASA history is not available from a valid local cache; no climate fit is inferred.")
                    scope_notes_bn.append("জেলার NASA ইতিহাস যাচাইকৃত স্থানীয় ক্যাশে নেই; জলবায়ুর সঙ্গে মিল অনুমান করা হয়নি।")
            else:
                scope_notes_en.append("Record a canonical district to look up historical NASA context.")
                scope_notes_bn.append("NASA-র ঐতিহাসিক প্রেক্ষাপট দেখতে সঠিক জেলার নাম যোগ করুন।")

        not_assessed_en = [
            "NASA climate observations are not scored against these sequences; the separate planting-window view is climate context only.",
            "Exact planting dates, stage calendars, water amounts, labor, cost, yields, soil nutrients, carbon, erosion, and pest-cycle outcomes are not evaluated.",
            "A listed legume or green-manure crop does not establish a measured soil-health improvement or fertilizer saving.",
        ]
        not_assessed_bn = [
            "এই বিন্যাসগুলোর সঙ্গে NASA জলবায়ুর তথ্য মিলিয়ে স্কোর করা হয়নি; আলাদা রোপণ-সময়ের অংশটি শুধু জলবায়ুর প্রেক্ষাপট দেখায়।",
            "নির্দিষ্ট রোপণের তারিখ, বৃদ্ধির ধাপের ক্যালেন্ডার, পানির পরিমাণ, শ্রম, খরচ, ফলন, মাটির পুষ্টি, কার্বন, ক্ষয় ও পোকা-চক্রের ফল যাচাই করা হয়নি।",
            "তালিকায় ডাল বা সবুজ সার থাকলেই মাটির স্বাস্থ্য উন্নতি বা সারের সাশ্রয় পরিমাপ হয়েছে—এমন নয়।",
        ]

        if outside_scope:
            status = "outside_documented_scope"
            message_en = "The farm profile does not match the land, soil, and irrigation conditions BRRI lists for these patterns, so they are not shown as options."
            message_bn = "খামারের জমি, মাটি ও সেচের তথ্য BRRI-র এই বিন্যাসগুলোর শর্তের সঙ্গে মেলে না; তাই এগুলো বিকল্প হিসেবে দেখানো হচ্ছে না।"
        elif unknowns_en:
            status = "insufficient_evidence"
            message_en = "Some farm conditions needed to check these published patterns are missing. Add or confirm them before comparing options."
            message_bn = "প্রকাশিত এই বিন্যাসগুলোর সঙ্গে খামারের মিল যাচাই করতে কিছু তথ্য নেই। বিকল্প তুলনার আগে তথ্য যোগ বা নিশ্চিত করুন।"
        elif not current_sequence:
            status = "insufficient_evidence"
            message_en = "BRRI patterns matching the saved farm conditions are shown, but no active or completed crop seasons are recorded for a baseline comparison."
            message_bn = "সংরক্ষিত খামারের শর্তের সঙ্গে মেলে এমন BRRI বিন্যাস দেখানো হয়েছে, তবে তুলনার ভিত্তি হিসেবে কোনো চলমান বা সম্পন্ন মৌসুম নথিভুক্ত নেই।"
            unknowns_en.append("Record an active or completed season to compare with the farm's own crop sequence.")
            unknowns_bn.append("নিজের ফসলের ধারার সঙ্গে তুলনা করতে একটি চলমান বা সম্পন্ন মৌসুম নথিভুক্ত করুন।")
        else:
            status = "available"
            message_en = "These are two BRRI-published patterns within the saved farm profile's stated scope, alongside recorded farm seasons. They are comparison examples, not a ranked recommendation."
            message_bn = "সংরক্ষিত খামারের শর্তের আওতায় থাকা BRRI-প্রকাশিত দুটি বিন্যাস ও নথিভুক্ত মৌসুম দেখানো হয়েছে। এগুলো তুলনার উদাহরণ, ক্রমানুসারে দেওয়া সুপারিশ নয়।"

        return RotationComparison(
            contract_version=CONTRACT_VERSION,
            farmland_id=snapshot.farmland_id,
            status=status,
            message_en=message_en,
            message_bn=message_bn,
            current_sequence=current_sequence,
            current_sequence_basis=current_sequence_basis,
            farmer_reported_previous_crop=snapshot.profile.previous_crop,
            alternatives=alternatives,
            strategies=strategies,
            evidence=evidence,
            unknowns_en=unknowns_en,
            unknowns_bn=unknowns_bn,
            scope_notes_en=scope_notes_en,
            scope_notes_bn=scope_notes_bn,
            not_assessed_en=not_assessed_en,
            not_assessed_bn=not_assessed_bn,
            selection_allowed=False,
            climate_evidence=climate_evidence,
            climate_status=climate_status,
            recorded_history=snapshot.rotation_history,
            active_season=snapshot.active_season,
            created_at=created_at,
        )

    @staticmethod
    def _current_sequence(snapshot: FarmProfileSnapshot) -> tuple[list[str], str]:
        # The reader returns completed seasons newest first; reverse to display
        # chronological order, then append the currently active crop.
        history = list(reversed(snapshot.rotation_history))
        sequence = [item.crop_code for item in history]
        active_crop = (
            snapshot.active_season.crop_code
            if snapshot.active_season is not None
            else None
        )
        if active_crop:
            sequence.append(active_crop)
            basis = "active_and_completed_seasons" if history else "active_season_only"
        else:
            basis = "completed_seasons_only" if history else "not_recorded"
        return sequence[-12:], basis

    @staticmethod
    def _profile_gaps(
        snapshot: FarmProfileSnapshot,
        catalog: dict[str, Any],
    ) -> tuple[list[str], list[str], list[str], list[str], bool]:
        profile = snapshot.profile
        match = catalog["profile_match"]
        missing_en: list[str] = []
        missing_bn: list[str] = []
        scope_notes_en: list[str] = []
        scope_notes_bn: list[str] = []
        outside_scope = False

        if profile.irrigation_available is None:
            missing_en.append("Confirm whether irrigation is available.")
            missing_bn.append("সেচের ব্যবস্থা আছে কি না নিশ্চিত করুন।")
        elif profile.irrigation_available != match["irrigation_available"]:
            outside_scope = True
            scope_notes_en.append("BRRI lists these patterns for irrigated land; the saved profile says irrigation is unavailable.")
            scope_notes_bn.append("BRRI এই বিন্যাসগুলো সেচযুক্ত জমির জন্য উল্লেখ করেছে; সংরক্ষিত তথ্যে সেচ নেই বলা হয়েছে।")

        land_type = _normalize(profile.land_type)
        if land_type is None:
            missing_en.append("Add the farm's land type (high or medium-high is needed for this source pattern).")
            missing_bn.append("জমির ধরন যোগ করুন (এই উৎসের বিন্যাসের জন্য উঁচু বা মাঝারি উঁচু জমি দরকার)।")
        elif land_type not in {_normalize(value) for value in match["land_types"]}:
            outside_scope = True
            scope_notes_en.append("The recorded land type is outside the high or medium-high land scope of this source pattern.")
            scope_notes_bn.append("নথিভুক্ত জমির ধরন এই উৎসের উঁচু বা মাঝারি উঁচু জমির আওতার বাইরে।")

        soil_type = _normalize(profile.soil_type)
        if soil_type is None:
            missing_en.append("Add the farm's soil type (clay or clay loam is needed for this source pattern).")
            missing_bn.append("মাটির ধরন যোগ করুন (এই উৎসের বিন্যাসের জন্য এঁটেল বা এঁটেল দোআঁশ মাটি দরকার)।")
        elif soil_type not in {_normalize(value) for value in match["soil_types"]}:
            outside_scope = True
            scope_notes_en.append("The recorded soil type is outside the clay or clay-loam scope of this source pattern.")
            scope_notes_bn.append("নথিভুক্ত মাটির ধরন এই উৎসের এঁটেল বা এঁটেল দোআঁশ মাটির আওতার বাইরে।")

        return missing_en, missing_bn, scope_notes_en, scope_notes_bn, outside_scope

    @staticmethod
    def _provenance(catalog: dict[str, Any]) -> SourceProvenance:
        source = catalog["source"]
        captured_on = date.fromisoformat(catalog["captured_on"])
        captured_at = datetime.combine(captured_on, time.min, tzinfo=timezone.utc)
        return SourceProvenance(
            source_id=source["source_id"],
            source_name=source["title"],
            source_url=source["url"],
            dataset_version=f"page-updated-{source['updated_on']}",
            retrieved_at=captured_at,
            recorded_at=captured_at,
            method="third_party",
            license=None,
            temporal_start=None,
            temporal_end=None,
            quality_status="provisional",
        )

    @staticmethod
    def _calendar_evidence(step: RotationSequenceStep) -> RotationStepCalendarEvidence:
        candidates = [calendar_reference_for_variety(step.crop_code, name) for name in step.variety_names]
        candidates = [item for item in candidates if item is not None and item.season.casefold() == step.season_code.casefold()]
        if not candidates:
            return RotationStepCalendarEvidence(
                status="not_available",
                gaps_en=["No inspected cultivar/season calendar matches this step; its dates and stage schedule remain unavailable."],
                gaps_bn=["এই ধাপের জাত ও মৌসুমের সঙ্গে মেলে এমন পরিদর্শিত ক্যালেন্ডার নেই; তারিখ ও বৃদ্ধির ধাপের সময়সূচি অনুপলব্ধ।"],
            )
        matching = [item for item in candidates if item.cultivation_method == step.cultivation_method]
        if not matching:
            return RotationStepCalendarEvidence(
                status="cultivation_method_mismatch",
                gaps_en=["Available references use a different establishment method; transplanted dates cannot be assigned to wet-seeded rice."],
                gaps_bn=["পাওয়া তথ্যের চাষের পদ্ধতি আলাদা; চারা রোপণের তারিখ ভেজা বোনা ধানের জন্য বসানো যাবে না।"],
            )
        return RotationStepCalendarEvidence(
            status="source_reference_available", references=matching,
            gaps_en=["Only the displayed variety alternatives have a source reference; no variety is selected. Agronomic review and a complete stage calendar remain pending."],
            gaps_bn=["শুধু দেখানো জাতগুলোর তথ্যসূত্র পাওয়া গেছে; কোনো জাত নির্বাচন করা হয়নি। কৃষিবিদের পর্যালোচনা ও পূর্ণ বৃদ্ধির ধাপের ক্যালেন্ডার বাকি।"],
        )

    @staticmethod
    def _strategy(
        pattern: dict[str, Any],
        steps: list[RotationSequenceStep],
        catalog: dict[str, Any],
    ) -> RotationStrategy:
        steps = [step.model_copy(update={"calendar_evidence": BrriRotationComparisonProvider._calendar_evidence(step)}) for step in steps]
        evidence_id = pattern["pattern_id"]
        evidence_ids = [evidence_id, catalog["source"]["source_id"]]
        tradeoffs = [
            RotationTradeoff(
                dimension="sequence_length",
                evidence_status="derived_from_sequence",
                label_en="Crops listed in this sequence",
                label_bn="এই ধারায় তালিকাভুক্ত ফসলের সংখ্যা",
                detail_en=(
                    f"The source lists {len(steps)} crop or green-manure steps. This is a sequence count, not a measure of workload, cost, or cropping intensity on your field."
                ),
                detail_bn=(
                    f"উৎসে {len(steps)}টি ফসল বা সবুজ সারের ধাপ আছে। এটি শুধু ধারার ধাপের সংখ্যা; আপনার জমির শ্রম, খরচ বা ফসলের তীব্রতার মাপ নয়।"
                ),
                evidence_ids=[evidence_id],
            )
        ]
        chickpea_present = any(step.crop_code == "chickpea" for step in steps)
        tradeoffs.append(
            RotationTradeoff(
                dimension="legume",
                evidence_status="source_documented" if chickpea_present else "derived_from_sequence",
                label_en="Chickpea in the sequence" if chickpea_present else "No chickpea step listed",
                label_bn="ধারায় ছোলা আছে" if chickpea_present else "ছোলার ধাপ উল্লেখ নেই",
                detail_en=(
                    "Chickpea is named in this source pattern. The source does not quantify a soil-nitrogen change, fertilizer saving, or yield effect."
                    if chickpea_present
                    else "This source pattern does not list chickpea. This does not rank the soil-health effects of its other crops or green manure."
                ),
                detail_bn=(
                    "এই উৎসের বিন্যাসে ছোলার নাম আছে। মাটির নাইট্রোজেন, সারের সাশ্রয় বা ফলনের পরিবর্তন উৎসে পরিমাপ করা হয়নি।"
                    if chickpea_present
                    else "এই উৎসের বিন্যাসে ছোলা তালিকাভুক্ত নেই। এতে অন্য ফসল বা সবুজ সারের মাটির স্বাস্থ্যের প্রভাবের ক্রম নির্ধারণ করা হয়নি।"
                ),
                evidence_ids=[evidence_id],
            )
        )
        green_manure_present = any(step.crop_role == "green_manure" for step in steps)
        tradeoffs.append(
            RotationTradeoff(
                dimension="green_manure",
                evidence_status="source_documented" if green_manure_present else "derived_from_sequence",
                label_en="Green manure included" if green_manure_present else "No green-manure step listed",
                label_bn="সবুজ সার অন্তর্ভুক্ত" if green_manure_present else "সবুজ সারের ধাপ উল্লেখ নেই",
                detail_en=(
                    "Sesbania rostrata is listed as green manure. The source does not quantify soil improvement or a fertilizer credit."
                    if green_manure_present
                    else "This source pattern does not list a green-manure step; no soil-health ranking is inferred."
                ),
                detail_bn=(
                    "ধৈঞ্চা (Sesbania rostrata) সবুজ সার হিসেবে তালিকাভুক্ত। মাটির উন্নতি বা সারের সাশ্রয়ের পরিমাণ উৎসে নেই।"
                    if green_manure_present
                    else "এই উৎসের বিন্যাসে সবুজ সারের ধাপ নেই; মাটির স্বাস্থ্য নিয়ে কোনো ক্রম নির্ধারণ করা হয়নি।"
                ),
                evidence_ids=[evidence_id],
            )
        )
        source = catalog["source"]
        return RotationStrategy(
            strategy_id=pattern["pattern_id"],
            name_en=pattern["name_en"],
            name_bn=pattern["name_bn"],
            applicability_status="matches_documented_scope",
            documented_scope_en=source["source_scope_en"],
            documented_scope_bn=source["source_scope_bn"],
            steps=steps,
            tradeoffs=tradeoffs,
            evidence_ids=evidence_ids,
        )
