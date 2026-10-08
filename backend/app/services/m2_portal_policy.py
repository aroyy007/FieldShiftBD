"""Automated acceptance policies for BARC Agri-Advisory Portal evidence (M2).

No human reviewer is available, so these policies accept only facts that a
program can check against pinned captures of the official BARC portal:

``m2-barc-portal-bilingual-v1``
    Land/soil conditions, maturity indicators, and seasonal harvest periods.
    Every claimed value must be stated by BOTH the English and the Bangla text
    of the same portal record (outside negated sentences). The portal's two
    language versions often disagree; disagreeing or single-language values
    are not accepted.

``m2-barc-portal-variety-duration-v1``
    A variety's published duration range (structured numeric fields), within
    plausibility bounds, for directly planted crops only.

``m2-barc-czs-upazila-suitability-v1``
    Upazila aggregate distribution across BARC suitability classes. It is
    stored as ``regional_context_only`` and never establishes a farm-level fit.

Every accepted row expires 180 days after its capture date. Read-time checks
rebuild the expected row from the pinned capture and the claim manifest, so an
edited database row, an edited claim, or a changed capture is rejected.
Automated acceptance never sets ``reviewed_by``/``reviewed_at``.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from app.models.core import AgriculturalKnowledge
from app.services.m1_reference import (
    crop_definition,
    crop_key_for_name,
    geography,
    normalize_text,
    normalize_variety_name,
)
from app.services.source_captures import SourceCaptureError, capture_entry, read_verified_bytes, read_verified_json

CLAIMS_PATH = Path(__file__).resolve().parents[1] / "data" / "m2_knowledge_sources" / "barc_portal_claims.json"

BILINGUAL_POLICY_ID = "m2-barc-portal-bilingual-v1"
VARIETY_POLICY_ID = "m2-barc-portal-variety-duration-v1"
REGIONAL_POLICY_ID = "m2-barc-czs-upazila-suitability-v1"
PORTAL_POLICY_IDS = frozenset({BILINGUAL_POLICY_ID, VARIETY_POLICY_ID, REGIONAL_POLICY_ID})
REFRESH_DAYS = 180
SOURCE_TYPE = "government_advisory_portal"
PORTAL_SOURCE_NAME = "BARC Agri-Advisory Portal"
CZS_SOURCE_NAME = "BARC Crop Zoning — upazila crop suitability"
_PORTAL_HOST = "portal.cropzoning.gov.bd"
_CZS_HOST = "api1.cropzoning.gov.bd"
_LICENSE_SENTENCE = "may be reproduced free of charge in any format or media without requiring specific permission"
_DIRECT_PLANTED_CROPS = frozenset({"potato", "wheat", "maize"})
_SUITABILITY_CLASSES = (
    ("vs", "very_suitable", "80-100%"),
    ("s", "suitable", "60-80%"),
    ("ms", "moderately_suitable", "40-60%"),
    ("ls", "marginally_suitable", "20-40%"),
    ("ns", "not_suitable", "0-20%"),
)


class PortalPolicyError(ValueError):
    """A claim or capture does not satisfy the BARC portal acceptance policy."""


# ── Term detection ───────────────────────────────────────────────────────────

_EN_LAND = (
    (r"very\s+low\s*land", "very_low"),
    (r"medium\s+high", "medium_high"),
    (r"medium\s+low", "medium_low"),
    (r"high\s*land", "high"),
    (r"low\s*land", "low"),
)
_EN_LAND_BARE = ((r"\bhigh\b", "high"), (r"\blow\b", "low"))
_BN_LAND = (
    ("অতি নিচু", "very_low"),
    ("অতিনিচু", "very_low"),
    ("মাঝারি উচু", "medium_high"),
    ("মাঝারি নিচু", "medium_low"),
    ("উচু", "high"),
    ("নিচু", "low"),
)
_EN_SOIL = (
    (r"silty\s+clay\s+loam", "silty_clay_loam"),
    (r"sandy\s+clay\s+loam", "sandy_clay_loam"),
    (r"sandy\s+loam", "sandy_loam"),
    (r"clay\s+loam", "clay_loam"),
    (r"silt\s+loam", "silt_loam"),
    (r"loamy\s+sand", "loamy_sand"),
    (r"heavy\s+clay", "heavy_clay"),
    (r"\bloamy\b", "loam"),
    (r"\bloam\b", "loam"),
    (r"\bsandy\b", "sand"),
    (r"\bsand\b", "sand"),
    (r"\bclay\b", "clay"),
    (r"\bsilty?\b", "silt"),
)
_BN_SOIL = (
    ("বেলে দোআশ", "sandy_loam"),
    ("এটেল দোআশ", "clay_loam"),
    ("পলি দোআশ", "silt_loam"),
    ("দোআশ", "loam"),
    ("এটেল", "clay"),
    ("বেলে", "sand"),
    ("পলি", "silt"),
)
_EN_NEGATION = re.compile(r"\b(except|not|unsuitable|avoid)\b")
_BN_NEGATION = ("ছাড়া", "ছাড়া", "নয়", "নয়", "অনুপযোগি")
_EN_INDICATORS = ((r"\bgolden\b", "golden_colour"),)
_BN_INDICATORS = (("সোনালি", "golden_colour"),)
_EN_SEASONS = ((r"\bkharif[\s\-]*(?:1|i)\b", "kharif_1"), (r"\bkharif[\s\-]*(?:2|ii)\b", "kharif_2"), (r"\brabi\b", "rabi"))
_BN_SEASONS = (("খরিপ ১", "kharif_1"), ("খরিফ ১", "kharif_1"), ("খরিপ ২", "kharif_2"), ("খরিফ ২", "kharif_2"), ("রবি", "rabi"))
_EN_MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
_BN_MONTHS = (
    "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
    "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
)
_BN_LETTER = "ঀ-৿"


def _bn_normalize(text: str) -> str:
    text = normalize_text(text).replace("‌", "").replace("‍", "")
    return text.replace("দো আশ", "দোআশ")


def _sentences(text: str) -> list[str]:
    return [part for part in re.split(r"[.\n;।]+", text) if part.strip()]


def _detect_en(text: str, patterns, bare=()) -> set[str]:
    found: set[str] = set()
    for sentence in _sentences(text.casefold()):
        if _EN_NEGATION.search(sentence):
            continue
        remaining = sentence
        for pattern, code in patterns:
            if re.search(pattern, remaining):
                found.add(code)
                remaining = re.sub(pattern, " ", remaining)
        if "land" in sentence:
            for pattern, code in bare:
                if re.search(pattern, remaining):
                    found.add(code)
    return found


def _detect_bn(text: str, terms) -> set[str]:
    found: set[str] = set()
    for sentence in _sentences(_bn_normalize(text)):
        if any(cue in sentence for cue in _BN_NEGATION):
            continue
        remaining = sentence
        for term, code in terms:
            if term in remaining:
                found.add(code)
                remaining = remaining.replace(term, " ")
    return found


def corroborated_land_types(en_text: str, bn_text: str) -> set[str]:
    return _detect_en(en_text, _EN_LAND, _EN_LAND_BARE) & _detect_bn(bn_text, _BN_LAND)


def corroborated_soil_textures(en_text: str, bn_text: str) -> set[str]:
    return (_detect_en(en_text, _EN_SOIL) & _detect_bn(bn_text, _BN_SOIL)) - {"heavy_clay"}


def corroborated_indicators(en_text: str, bn_text: str) -> set[str]:
    return _detect_en(en_text, _EN_INDICATORS) & _detect_bn(bn_text, _BN_INDICATORS)


def _line_periods_en(text: str) -> list[tuple[set[str], set[int]]]:
    result = []
    for line in text.casefold().splitlines():
        seasons = {code for pattern, code in _EN_SEASONS if re.search(pattern, line)}
        months = {index + 1 for index, name in enumerate(_EN_MONTHS) if re.search(rf"\b{name}\b", line)}
        result.append((seasons, months))
    return result


def _line_periods_bn(text: str) -> list[tuple[set[str], set[int]]]:
    result = []
    for line in text.splitlines():
        normalized = _bn_normalize(line)
        seasons = {code for term, code in _BN_SEASONS if term in normalized}
        months = set()
        for index, name in enumerate(_BN_MONTHS):
            month = _bn_normalize(name)
            suffix_guard = f"(?![{_BN_LETTER}])" if month == "মে" else ""
            if re.search(f"(?<![{_BN_LETTER}]){re.escape(month)}{suffix_guard}", normalized):
                months.add(index + 1)
        result.append((seasons, months))
    return result


def period_corroborated(en_text: str, bn_text: str, season: str, months: list[int]) -> bool:
    wanted = set(months)

    def supported(lines):
        return any(season in seasons and wanted <= line_months for seasons, line_months in lines)

    return bool(wanted) and supported(_line_periods_en(en_text)) and supported(_line_periods_bn(bn_text))


# ── Shared helpers ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def claims_manifest() -> dict[str, Any]:
    return json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))


def _claim_spec(claim_id: str) -> dict[str, Any]:
    claim = next((item for item in claims_manifest()["claims"] if item["claim_id"] == claim_id), None)
    if claim is None:
        raise PortalPolicyError(f"claim {claim_id} is not in the claim manifest")
    return claim


def knowledge_row_id(policy_id: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://fieldshiftbd.local/m2/{policy_id}/{key}")


def _same_json(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, ensure_ascii=False, default=str) == json.dumps(
        right, sort_keys=True, ensure_ascii=False, default=str
    )


def _capture_provenance(relative_path: str, host: str, route_pattern: str) -> dict[str, Any]:
    entry = capture_entry(relative_path)
    read_verified_bytes(relative_path)
    parsed = urlparse(entry["url"])
    if parsed.scheme != "https" or parsed.hostname != host or not re.fullmatch(route_pattern, parsed.path):
        raise PortalPolicyError(f"{relative_path} was not captured from the expected official BARC route")
    if parsed.query or parsed.fragment:
        raise PortalPolicyError(f"{relative_path} has an unexpected query string")
    retrieved_on = datetime.fromisoformat(entry["retrieved_at"]).date()
    return {
        "capture_path": relative_path,
        "url": entry["url"],
        "retrieved_at": entry["retrieved_at"],
        "retrieved_on": retrieved_on.isoformat(),
        "sha256": entry["sha256"],
    }


def _check_license() -> None:
    license_path = claims_manifest()["source"]["license_capture"]
    entry = capture_entry(license_path)
    if urlparse(entry["url"]).hostname != _PORTAL_HOST:
        raise PortalPolicyError("license capture is not from the BARC portal")
    if _LICENSE_SENTENCE not in read_verified_bytes(license_path).decode("utf-8", "replace"):
        raise PortalPolicyError("the captured portal copyright policy no longer grants free reproduction")


def _freshness(retrieved_on: date, evaluated_on: date) -> None:
    age = (evaluated_on - retrieved_on).days
    if age < 0:
        raise PortalPolicyError("capture is dated after the evaluation date")
    if age > REFRESH_DAYS:
        raise PortalPolicyError(f"capture is older than the {REFRESH_DAYS}-day refresh window")


def _policy_block(policy_id: str, evaluated_on: date, retrieved_on: str, checks: list[str], limitations: list[str]) -> dict[str, Any]:
    return {
        "id": policy_id,
        "version": 1,
        "method": "automated_source_validation",
        "evaluated_on": evaluated_on.isoformat(),
        "retrieved_on": retrieved_on,
        "checks_passed": sorted(checks),
        "limitations": limitations,
    }


def _source_block(provenance: Mapping[str, Any], page_url: str) -> dict[str, Any]:
    source = claims_manifest()["source"]
    return {
        "publisher": source["publisher"],
        "page_url": page_url,
        "api_url": provenance["url"],
        "retrieved_at": provenance["retrieved_at"],
        "capture_sha256": provenance["sha256"],
        "capture_path": provenance["capture_path"],
        "license": source["license_summary"],
        "publisher_disclaimer": source["disclaimer"],
    }


def _crop_matches(crop_key: str, crop_name: str | None) -> bool:
    return crop_name is not None and crop_key_for_name(crop_name) == crop_key


# ── Bilingual production-technology claims ───────────────────────────────────

_BILINGUAL_LIMITATIONS = [
    "Only values stated in both the English and Bangla portal text are accepted.",
    "General Bangladesh advisory; not specific to a district, upazila, or field.",
    "The record expires 180 days after capture unless the portal is re-captured and re-verified.",
]


def _verify_bilingual(claim: Mapping[str, Any], record: Mapping[str, Any]) -> list[str]:
    definition = crop_definition(claim["crop_key"])
    if definition is None or record.get("crop_id") not in definition["portal_crop_ids"]:
        raise PortalPolicyError(f"{claim['claim_id']}: portal record is not for {claim['crop_key']}")
    en_text = record.get(claim["fields"]["en"])
    bn_text = record.get(claim["fields"]["bn"])
    if not isinstance(en_text, str) or not en_text.strip() or not isinstance(bn_text, str) or not bn_text.strip():
        raise PortalPolicyError(f"{claim['claim_id']}: both language fields must contain text")
    values = claim["values"]
    claim_type = claim["claim_type"]
    if claim_type == "land_soil_condition":
        if claim["category"] != "crop_suitability":
            raise PortalPolicyError("land/soil claims must use the crop_suitability category")
        for dimension, supported in (
            ("land_type", corroborated_land_types(en_text, bn_text)),
            ("soil_texture", corroborated_soil_textures(en_text, bn_text)),
        ):
            claimed = set(values.get(dimension) or [])
            if not claimed or not claimed <= supported:
                raise PortalPolicyError(
                    f"{claim['claim_id']}: {dimension} {sorted(claimed - supported) or 'missing'} is not stated in both languages"
                )
        return ["land_type_values_in_both_languages", "soil_texture_values_in_both_languages"]
    if claim_type == "maturity_indicator":
        claimed = set(values.get("indicators") or [])
        if not claimed or not claimed <= corroborated_indicators(en_text, bn_text):
            raise PortalPolicyError(f"{claim['claim_id']}: maturity indicator is not stated in both languages")
        return ["maturity_indicator_in_both_languages"]
    if claim_type == "seasonal_harvest_period":
        periods = values.get("periods") or []
        if not periods:
            raise PortalPolicyError(f"{claim['claim_id']}: no harvest periods claimed")
        for period in periods:
            if not period_corroborated(en_text, bn_text, period["season"], period["months"]):
                raise PortalPolicyError(
                    f"{claim['claim_id']}: {period['season']} months {period['months']} are not stated in both languages"
                )
        return ["season_and_months_in_both_languages"]
    raise PortalPolicyError(f"unsupported claim type {claim_type}")


def build_bilingual_content(claim: Mapping[str, Any], evaluated_on: date) -> tuple[dict[str, Any], dict[str, Any]]:
    _check_license()
    provenance = _capture_provenance(claim["capture"], _PORTAL_HOST, r"/api/crop/get-prod-tech/\d+")
    _freshness(date.fromisoformat(provenance["retrieved_on"]), evaluated_on)
    record = read_verified_json(claim["capture"])
    checks = _verify_bilingual(claim, record)
    checks += [
        "trusted_https_publisher_route",
        "capture_sha256_matches_manifest",
        "publisher_license_permits_reproduction",
        "claim_matches_manifest",
        f"capture_within_{REFRESH_DAYS}_day_refresh_window",
    ]
    en_text = record[claim["fields"]["en"]]
    bn_text = record[claim["fields"]["bn"]]
    content: dict[str, Any] = {
        "source_type": SOURCE_TYPE,
        "factor": "land_and_soil" if claim["claim_type"] == "land_soil_condition" else "harvest",
        "evidence_role": "general_condition" if claim["claim_type"] == "land_soil_condition" else "harvest_guidance",
        "claim": dict(claim),
        "context": {
            "crop_key": claim["crop_key"],
            "geographic_scope": "Bangladesh (general advisory)",
            "portal_crop_id": record["crop_id"],
            "portal_record_id": record["id"],
            "portal_record_updated_at": record.get("updated_at"),
            "upstream_source": record.get("source"),
        },
        "evidence": {
            "en_field": claim["fields"]["en"],
            "bn_field": claim["fields"]["bn"],
            "en_text": en_text,
            "bn_text": bn_text,
            "accepted_values": claim["values"],
            "excluded_values": claim.get("excluded", []),
        },
        "source": _source_block(provenance, claim["page_url"]),
        "acceptance_policy": _policy_block(
            BILINGUAL_POLICY_ID, evaluated_on, provenance["retrieved_on"], checks, _BILINGUAL_LIMITATIONS
        ),
    }
    if claim["claim_type"] == "land_soil_condition":
        content["factors"] = {
            "land_and_soil": {
                "kind": "positive_factors",
                "when": {
                    "land_type": list(claim["values"]["land_type"]),
                    "soil_texture": list(claim["values"]["soil_texture"]),
                },
                "explanation": claim["explanation"],
            }
        }
    else:
        content["maturity_indicators"] = list(claim.get("maturity_indicators", []))
        content["guidance"] = list(claim.get("guidance", []))
        content["uncertainty_notes"] = list(claim.get("uncertainty_notes", []))
    return content, provenance


def build_bilingual_record(claim: Mapping[str, Any], crop_id: UUID, evaluated_on: date) -> AgriculturalKnowledge:
    content, provenance = build_bilingual_content(claim, evaluated_on)
    retrieved_on = date.fromisoformat(provenance["retrieved_on"])
    return AgriculturalKnowledge(
        id=knowledge_row_id(BILINGUAL_POLICY_ID, claim["claim_id"]),
        crop_id=crop_id,
        crop_variety_id=None,
        category=claim["category"],
        region_code="BD",
        content=content,
        source_name=PORTAL_SOURCE_NAME,
        source_reference=claim["page_url"],
        effective_from=retrieved_on,
        effective_to=retrieved_on + timedelta(days=REFRESH_DAYS),
        review_status="approved",
        reviewed_by=None,
        reviewed_at=None,
    )


# ── Variety durations ────────────────────────────────────────────────────────

_VARIETY_LIMITATIONS = [
    "The portal does not state the event the duration is counted from; FieldShift counts it from the season's planting date.",
    "Published variety duration, not a forecast for a specific field or season.",
    "The record expires 180 days after capture unless re-captured.",
]


def build_variety_content(crop_key: str, portal_variety_id: int, evaluated_on: date) -> dict[str, Any]:
    if crop_key not in _DIRECT_PLANTED_CROPS:
        raise PortalPolicyError(f"variety durations are not accepted for {crop_key}")
    config = claims_manifest()["variety_duration"]
    capture = config["capture_pattern"].format(portal_variety_id=portal_variety_id)
    provenance = _capture_provenance(capture, _PORTAL_HOST, r"/api/get-variety-by-id/\d+")
    _freshness(date.fromisoformat(provenance["retrieved_on"]), evaluated_on)
    _check_license()
    record = read_verified_json(capture)
    definition = crop_definition(crop_key)
    if record.get("id") != portal_variety_id or record.get("crop_id") not in definition["portal_crop_ids"]:
        raise PortalPolicyError(f"variety {portal_variety_id} is not a {crop_key} record")
    low, high = record.get("duration_days_from"), record.get("duration_days_to") or record.get("duration_days_from")
    bounds = config["bounds_days"]
    if (
        isinstance(low, bool) or not isinstance(low, int) or not isinstance(high, int)
        or not bounds["min"] <= low <= high <= bounds["max"]
    ):
        raise PortalPolicyError(f"variety {portal_variety_id} has no plausible duration range")
    name = normalize_variety_name(str(record["name"]))
    portal_crop_id = record["crop_id"]
    range_text = f"{low}" if low == high else f"{low}–{high}"
    return {
        "source_type": SOURCE_TYPE,
        "factor": "variety_duration",
        "evidence_role": "harvest_guidance",
        "claim": {
            "claim_type": config["claim_type"],
            "crop_key": crop_key,
            "portal_variety_id": portal_variety_id,
            "variety_name": name,
        },
        "context": {"crop_key": crop_key, "variety_name": name, "geographic_scope": "Bangladesh (general advisory)"},
        "evidence": {
            "duration_days_from": low,
            "duration_days_to": high,
            "release_year": record.get("release_year"),
            "portal_record_updated_at": record.get("updated_at"),
            "publisher_is_active_flag": record.get("is_active"),
        },
        "harvest_window_days_after_planting": {"min": low, "max": high},
        "guidance": [f"BARC's Agri-Advisory Portal lists a duration of {range_text} days for {name}."],
        "uncertainty_notes": list(_VARIETY_LIMITATIONS[:2]) + [
            "Weather, planting date, and crop management shift maturity; confirm crop maturity in the field before harvesting."
        ],
        "source": _source_block(provenance, config["page_url"].format(portal_crop_id=portal_crop_id)),
        "acceptance_policy": _policy_block(
            VARIETY_POLICY_ID, evaluated_on, provenance["retrieved_on"],
            [
                "trusted_https_publisher_route",
                "capture_sha256_matches_manifest",
                "publisher_license_permits_reproduction",
                "variety_belongs_to_catalog_crop",
                "duration_range_within_bounds",
                f"capture_within_{REFRESH_DAYS}_day_refresh_window",
            ],
            _VARIETY_LIMITATIONS,
        ),
    }


def build_variety_record(
    crop_key: str, portal_variety_id: int, crop_id: UUID, crop_variety_id: UUID, evaluated_on: date
) -> AgriculturalKnowledge:
    content = build_variety_content(crop_key, portal_variety_id, evaluated_on)
    retrieved_on = date.fromisoformat(content["acceptance_policy"]["retrieved_on"])
    return AgriculturalKnowledge(
        id=knowledge_row_id(VARIETY_POLICY_ID, f"{crop_key}/{portal_variety_id}"),
        crop_id=crop_id,
        crop_variety_id=crop_variety_id,
        category="harvest_guidance",
        region_code="BD",
        content=content,
        source_name=PORTAL_SOURCE_NAME,
        source_reference=content["source"]["page_url"],
        effective_from=retrieved_on,
        effective_to=retrieved_on + timedelta(days=REFRESH_DAYS),
        review_status="approved",
        reviewed_by=None,
        reviewed_at=None,
    )


# ── Upazila regional context ─────────────────────────────────────────────────

_REGIONAL_LIMITATIONS = [
    "Upazila aggregate across BARC suitability classes; it does not assess any individual field.",
    "The API does not state the area unit, so only shares of the mapped total are reported.",
    "Regional context can never establish a positive recommendation by itself.",
    "The record expires 180 days after capture unless re-captured.",
]


def _int_value(raw: Any) -> int:
    if isinstance(raw, bool):
        raise PortalPolicyError("suitability value is not a nonnegative integer")
    try:
        value = int(str(raw).strip())
    except ValueError as error:
        raise PortalPolicyError("suitability value is not a nonnegative integer") from error
    if value < 0 or str(value) != str(raw).strip():
        raise PortalPolicyError("suitability value is not a nonnegative integer")
    return value


def build_regional_content(crop_key: str, upazila_code: str, evaluated_on: date) -> dict[str, Any] | None:
    config = claims_manifest()["regional_context"]
    capture = config["capture_pattern"].format(upazila_code=upazila_code)
    provenance = _capture_provenance(capture, _CZS_HOST, rf"/api/crop-suitability/{re.escape(upazila_code)}")
    _freshness(date.fromisoformat(provenance["retrieved_on"]), evaluated_on)
    upazila = geography().upazilas.get(upazila_code)
    if upazila is None:
        raise PortalPolicyError(f"upazila {upazila_code} is not in the M1 geography reference")
    district = geography().districts[upazila.district_code]
    definition = crop_definition(crop_key)
    names = {name.casefold() for name in definition["suitability_api_names"]}
    entries = []
    for row in read_verified_json(capture):
        if str(row.get("crop_name", "")).strip().casefold() not in names:
            continue
        values = {label: _int_value(row.get(raw_key)) for raw_key, label, _ in _SUITABILITY_CLASSES}
        total = sum(values.values())
        if total <= 0:
            continue
        entries.append({
            "crop_name": str(row["crop_name"]).strip(),
            "crop_name_bn": row.get("crop_name_bn"),
            "season": str(row.get("crop_season", "")).strip(),
            "season_bn": row.get("crop_season_bn"),
            "situation": str(row.get("crop_var", "")).strip(),
            "situation_bn": row.get("crop_var_bn"),
            "class_values": values,
            "mapped_total": total,
            "class_shares_percent": {label: round(value * 100 / total, 1) for label, value in values.items()},
        })
    if not entries:
        return None
    entries.sort(key=lambda item: (item["season"], item["crop_name"], item["situation"]))
    return {
        "source_type": "government_research_portal",
        "factor": "regional_crop_zoning",
        "evidence_type": "upazila_aggregated_suitability_distribution",
        "evidence_role": "regional_context_only",
        "claim": {"claim_type": config["claim_type"], "crop_key": crop_key, "upazila_code": upazila_code},
        "applicability": {"country_code": "BD", "upazila_code": upazila_code},
        "context": {
            "crop_key": crop_key,
            "upazila_code": upazila_code,
            "upazila": upazila.name,
            "district_code": district.code,
            "district": district.name,
            "spatial_resolution": "upazila",
            "area_unit": None,
            "class_definitions": {label: share for _, label, share in _SUITABILITY_CLASSES},
        },
        "evidence": {"entries": entries},
        "source": _source_block(
            provenance,
            config["page_url"].format(district_code=district.code, upazila_code=upazila_code),
        ),
        "acceptance_policy": _policy_block(
            REGIONAL_POLICY_ID, evaluated_on, provenance["retrieved_on"],
            [
                "trusted_https_publisher_route",
                "capture_sha256_matches_manifest",
                "crop_names_match_catalog",
                "class_values_nonnegative_integers",
                "regional_context_cannot_establish_farm_level_fit",
                f"capture_within_{REFRESH_DAYS}_day_refresh_window",
            ],
            _REGIONAL_LIMITATIONS,
        ),
    }


def build_regional_record(crop_key: str, upazila_code: str, crop_id: UUID, evaluated_on: date) -> AgriculturalKnowledge | None:
    content = build_regional_content(crop_key, upazila_code, evaluated_on)
    if content is None:
        return None
    retrieved_on = date.fromisoformat(content["acceptance_policy"]["retrieved_on"])
    return AgriculturalKnowledge(
        id=knowledge_row_id(REGIONAL_POLICY_ID, f"{crop_key}/{upazila_code}"),
        crop_id=crop_id,
        crop_variety_id=None,
        category="crop_suitability",
        region_code=f"BD-UPZ-{upazila_code}",
        content=content,
        source_name=CZS_SOURCE_NAME,
        source_reference=content["source"]["page_url"],
        effective_from=retrieved_on,
        effective_to=retrieved_on + timedelta(days=REFRESH_DAYS),
        review_status="approved",
        reviewed_by=None,
        reviewed_at=None,
    )


# ── Read-time validation ─────────────────────────────────────────────────────

def _expected_record(row: Any, content: Mapping[str, Any]) -> AgriculturalKnowledge | None:
    policy = content.get("acceptance_policy")
    claim = content.get("claim")
    if not isinstance(policy, Mapping) or not isinstance(claim, Mapping):
        return None
    try:
        evaluated_on = date.fromisoformat(str(policy.get("evaluated_on")))
    except ValueError:
        return None
    policy_id = policy.get("id")
    if policy_id == BILINGUAL_POLICY_ID:
        spec = _claim_spec(str(claim.get("claim_id")))
        if not _same_json(spec, claim):
            return None
        return build_bilingual_record(spec, row.crop_id, evaluated_on)
    if policy_id == VARIETY_POLICY_ID:
        return build_variety_record(
            str(claim.get("crop_key")), int(claim.get("portal_variety_id")), row.crop_id,
            row.crop_variety_id, evaluated_on,
        )
    if policy_id == REGIONAL_POLICY_ID:
        return build_regional_record(str(claim.get("crop_key")), str(claim.get("upazila_code")), row.crop_id, evaluated_on)
    return None


def is_valid_portal_acceptance(row: Any, content: Mapping[str, Any], *, crop_name: str | None = None) -> bool:
    """Rebuild the row from pinned evidence and require an exact match."""
    policy = content.get("acceptance_policy")
    claim = content.get("claim")
    if not isinstance(policy, Mapping) or policy.get("id") not in PORTAL_POLICY_IDS:
        return False
    if (
        row.review_status != "approved"
        or row.reviewed_by is not None
        or row.reviewed_at is not None
        or row.crop_id is None
        or not isinstance(claim, Mapping)
        or not _crop_matches(str(claim.get("crop_key")), crop_name)
    ):
        return False
    try:
        expected = _expected_record(row, content)
    except (PortalPolicyError, SourceCaptureError, KeyError, TypeError, ValueError):
        return False
    if expected is None:
        return False
    return (
        _same_json(expected.content, content)
        and row.category == expected.category
        and row.region_code == expected.region_code
        and row.source_name == expected.source_name
        and row.source_reference == expected.source_reference
        and row.effective_from == expected.effective_from
        and row.effective_to == expected.effective_to
        and (row.crop_variety_id is None) == (expected.crop_variety_id is None)
    )


def portal_acceptance_method(content: Mapping[str, Any]) -> str | None:
    policy = content.get("acceptance_policy")
    if isinstance(policy, Mapping) and policy.get("id") in PORTAL_POLICY_IDS:
        return f"automated_source_policy:{policy['id']}:v{policy.get('version', 1)}"
    return None
