"""Published agronomy facts; separate from approved operational knowledge."""

from functools import lru_cache
import json
from pathlib import Path
import re

from app.schemas.planting_window import VarietyCalendarReference

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data/m2_knowledge_sources/brri_crop_calendar_references.json"


def _variety_key(value: str) -> str:
    return re.sub(r"[^a-z0-9\u0980-\u09ff]", "", value.casefold())


@lru_cache(maxsize=1)
def _references() -> tuple[VarietyCalendarReference, ...]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    references = []
    for profile in catalog["profiles"]:
        source = profile["source"]
        scope = profile["scope"]
        references.append(VarietyCalendarReference(
            profile_id=profile["profile_id"],
            variety_name=profile["variety_name"],
            variety_name_bn=profile["variety_name_bn"],
            season=profile["season_code"].capitalize(),
            cultivation_method=profile["cultivation_method"],
            review_status=profile["review_status"],
            activation_allowed=profile["activation_allowed"],
            seedbed_window=profile["seedbed_window"],
            seedling_age_days=profile["seedling_age_days"],
            transplanting_window=profile["transplanting_window"],
            reported_life_duration_days=profile["reported_life_duration_days"],
            harvest_window=profile["harvest_window"],
            duration_reference_event=profile["duration_reference_event"],
            care_references=profile["care_references"],
            gdd_reference=profile["gdd"],
            excluded_ambiguities=profile["excluded_ambiguities"],
            geographic_scope_bn=scope["published_scope_bn"],
            geographic_scope_en=scope["published_scope_en"],
            source_name=source["name"],
            source_url=source["url"],
            source_accessed=source["accessed_on"],
            limitations_bn=[
                "এটি প্রকাশিত জাতের তথ্য; আপনার জমির উপযোগিতা ও কৃষিবিদের পর্যালোচনা বাকি।",
                "রোপণের সময় NASA তথ্য দিয়ে বদলানো হয়নি। এই তথ্য থেকে স্বয়ংক্রিয় মৌসুম বা কাজ তৈরি হয় না।",
                "জাতের যাচাইকৃত GDD ভিত্তি, সর্বোচ্চ তাপমাত্রা ও তাপ-লক্ষ্যমাত্রা নেই। জীবনকালের শুরুর ধাপও উৎসে স্পষ্ট নয়।",
            ],
            limitations_en=[
                "Published variety reference; field applicability and agronomic review are pending.",
                "No NASA-adjusted planting window, season activation or operational tasks are authorized.",
                "Cultivar GDD base/cap/target and the life-duration reference event are not established.",
            ],
        ))
    return tuple(references)


def published_calendar_references(crop: str, season: str | None = None) -> list[VarietyCalendarReference]:
    if crop.casefold().strip() not in {"rice", "ধান"}:
        raise ValueError("No published calendar references for this crop")
    season_key = season.casefold().strip() if season else None
    if season_key is not None and season_key not in {"aman", "boro", "aus"}:
        raise ValueError("Season must be aman, boro, or aus")
    return [item.model_copy(deep=True) for item in _references()
            if season_key is None or item.season.casefold() == season_key]


def calendar_reference_for_variety(crop: str, variety: str | None) -> VarietyCalendarReference | None:
    if not variety or crop.casefold().strip() not in {"rice", "ধান"}:
        return None
    key = _variety_key(variety)
    return next((item.model_copy(deep=True) for item in _references()
                 if key in {_variety_key(item.variety_name), _variety_key(item.variety_name_bn or "")}), None)
