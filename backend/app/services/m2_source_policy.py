"""Deterministic acceptance policy for narrowly scoped official M2 sources.

This module accepts a verified public BARC upazila crop-zoning snapshot. It
does not infer field-level suitability, season plans, growth stages, or harvest
guidance from the map.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID, uuid4

from app.models.core import AgriculturalKnowledge
from app.services.m2_portal_policy import (
    PORTAL_POLICY_IDS,
    is_valid_portal_acceptance,
    portal_acceptance_method,
)


BARC_POLICY_ID = "m2-barc-upazila-zoning-v1"
BARC_METHOD_URL = "https://apps.barc.gov.bd/cropzoning/homes/intro"
BARC_LICENSE_URL = "https://apps.barc.gov.bd/maps/index.php?t=crop_suitability"
BARC_REFRESH_DAYS = 180
_BARC_HOST = "apps.barc.gov.bd"
_BARC_MAP_CAPTURE_SHA256 = "FC863E8005F83C3DD3DD9CB009B640B8DACF8E9DD2243BCEDAE4B4DA7F0D624F"
_BARC_METHOD_CAPTURE_SHA256 = "AF1A35C8256C4867866D9E91C645E67D8B6B31EEB8ED777D4F1DF97603CE4D81"
_BARC_SOURCE_NAME = "BARC Crop Zoning — Potato, Comilla upazila"
_SUITABILITY_CLASSES = (
    "very_suitable",
    "suitable",
    "moderately_suitable",
    "marginally_suitable",
    "not_suitable",
)
_BARC_AREA_HECTARES = {
    "very_suitable": 1645,
    "suitable": 11020,
    "moderately_suitable": 2544,
    "marginally_suitable": 0,
    "not_suitable": 5364,
    "total": 20573,
}
_REQUIRED_CHECKS = frozenset({
    "trusted_https_publisher",
    "official_methodology_linked",
    "map_and_methodology_response_hashes_match_pinned_captures",
    "snapshot_payload_hash_matches_extracted_values",
    "crop_and_upazila_labels_match_source_route",
    "class_areas_are_nonnegative_and_sum_to_total",
    "regional_context_cannot_establish_farm_level_fit",
    "snapshot_within_180_day_refresh_window",
})
_POLICY_LIMITATIONS = [
    "BARC's source page does not state the underlying map data vintage.",
    "The source describes aggregated upazila area, not an individual farm.",
    "The record expires after 180 days unless refreshed from the source.",
    "This data supports regional crop potential only; it provides no season plan or harvest guidance.",
]


class SourcePolicyError(ValueError):
    """An official-source snapshot does not meet the M2 acceptance policy."""


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourcePolicyError(f"{field} must be a non-empty string")
    return value.strip()


def _official_barc_url(value: Any, path: str, field: str, expected_query: str = "") -> str:
    url = _required_text(value, field)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != _BARC_HOST or parsed.path != path:
        raise SourcePolicyError(f"{field} must be the expected official BARC HTTPS page")
    if parsed.query != expected_query or parsed.fragment:
        raise SourcePolicyError(f"{field} has an unexpected query string or fragment")
    return url


def _valid_sha256(value: Any, field: str) -> str:
    digest = _required_text(value, field)
    if re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
        raise SourcePolicyError(f"{field} must contain a SHA-256 digest")
    return digest.upper()


def _snapshot_sha256(snapshot: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def _same_json_value(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int equality coercion."""
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(
        right, sort_keys=True, separators=(",", ":")
    )


def _suitable_area_and_share(validated_snapshot: Mapping[str, Any]) -> tuple[int, float]:
    areas = validated_snapshot["area_hectares"]
    suitable_area = areas["very_suitable"] + areas["suitable"]
    return suitable_area, round(suitable_area / areas["total"] * 100, 2)


def _regional_zoning_explanation(validated_snapshot: Mapping[str, Any]) -> str:
    areas = validated_snapshot["area_hectares"]
    suitable_area, share = _suitable_area_and_share(validated_snapshot)
    return (
        "BARC's Potato suitability map for Comilla upazila, retrieved "
        f"{validated_snapshot['retrieved_on'].isoformat()} (dataset vintage is not published), "
        f"reports {areas['very_suitable']:,} ha very suitable and "
        f"{areas['suitable']:,} ha suitable: {suitable_area:,} of "
        f"{areas['total']:,} ha of mapped area ({share:.2f}%). This is "
        "upazila-level context only, not a field-level assessment or a guarantee "
        "for this farm."
    )


def _regional_zoning_factor(validated_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "kind": "regional_context",
        "when": {
            "country_code": validated_snapshot["country_code"],
            "district": validated_snapshot["district"],
            "upazila": validated_snapshot["upazila"],
        },
        "explanation": _regional_zoning_explanation(validated_snapshot),
    }


def _validate_page_extract(snapshot: Mapping[str, Any], areas: Mapping[str, int]) -> None:
    extracted = snapshot.get("page_extract")
    if not isinstance(extracted, Mapping):
        raise SourcePolicyError("page_extract must preserve the public map values")
    if extracted.get("title") != "Suitability Map of Potato [Comilla :: Comilla]":
        raise SourcePolicyError("map title does not match the selected crop and upazila")
    lines = extracted.get("area_lines")
    if not isinstance(lines, Mapping):
        raise SourcePolicyError("page_extract.area_lines must be an object")
    labels = {
        "very_suitable": "Very Suitable",
        "suitable": "Suitable",
        "moderately_suitable": "Moderately Suitable",
        "marginally_suitable": "Marginally Suitable",
        "not_suitable": "Not Suitable",
    }
    for key, label in labels.items():
        text = _required_text(lines.get(key), f"page_extract.area_lines.{key}")
        match = re.fullmatch(rf"{re.escape(label)}\s+Area:\s*([0-9,]+)\s+Hectre", text)
        if match is None or int(match.group(1).replace(",", "")) != areas[key]:
            raise SourcePolicyError(f"page extract disagrees with area_hectares.{key}")
    total_text = _required_text(lines.get("total"), "page_extract.area_lines.total")
    total_match = re.fullmatch(r"Total Area:\s*([0-9,]+)\s+Hectre", total_text)
    if total_match is None or int(total_match.group(1).replace(",", "")) != areas["total"]:
        raise SourcePolicyError("page extract disagrees with area_hectares.total")


def validate_barc_upazila_snapshot(
    snapshot: Mapping[str, Any], *, evaluated_on: date
) -> dict[str, Any]:
    """Validate and normalize an attributed BARC crop-zoning page snapshot."""
    if not isinstance(snapshot, Mapping):
        raise SourcePolicyError("snapshot must be an object")
    publisher = _required_text(snapshot.get("publisher"), "publisher")
    if publisher != "Bangladesh Agricultural Research Council (BARC)":
        raise SourcePolicyError("publisher is outside the configured source policy")

    crop_name = _required_text(snapshot.get("crop_name"), "crop_name")
    if crop_name.casefold() != "potato":
        raise SourcePolicyError("this policy currently supports Potato only")
    barc_crop_id = snapshot.get("barc_crop_id")
    if isinstance(barc_crop_id, bool) or barc_crop_id != 12:
        raise SourcePolicyError("source route does not identify the supported Potato map")

    region = snapshot.get("region")
    if not isinstance(region, Mapping):
        raise SourcePolicyError("region must be an object")
    country_code = _required_text(region.get("country_code"), "region.country_code")
    district = _required_text(region.get("district"), "region.district")
    upazila = _required_text(region.get("upazila"), "region.upazila")
    if (country_code, district.casefold(), upazila.casefold()) != ("BD", "comilla", "comilla"):
        raise SourcePolicyError("this policy currently supports the Comilla upazila snapshot only")
    barc_upazila_id = region.get("barc_upazila_id")
    if isinstance(barc_upazila_id, bool) or barc_upazila_id != 195:
        raise SourcePolicyError("source route does not identify Comilla upazila")

    source_url = _official_barc_url(
        snapshot.get("source_url"),
        "/cropzoning/homes/upazila/12/195",
        "source_url",
    )
    methodology_url = _official_barc_url(
        snapshot.get("methodology_url"),
        "/cropzoning/homes/intro",
        "methodology_url",
    )
    license_url = _official_barc_url(
        snapshot.get("license_url"),
        "/maps/index.php",
        "license_url",
        expected_query="t=crop_suitability",
    )
    license = _required_text(snapshot.get("license"), "license")
    if license != "CC BY 4.0":
        raise SourcePolicyError("source does not declare the expected BARC map license")

    try:
        retrieved_on = date.fromisoformat(_required_text(snapshot.get("retrieved_on"), "retrieved_on"))
    except ValueError as error:
        raise SourcePolicyError("retrieved_on must be an ISO date") from error
    age_days = (evaluated_on - retrieved_on).days
    if age_days < 0:
        raise SourcePolicyError("snapshot cannot be dated in the future")
    if age_days > BARC_REFRESH_DAYS:
        raise SourcePolicyError("snapshot is outside the 180-day refresh window")

    if snapshot.get("dataset_vintage") is not None:
        raise SourcePolicyError("this snapshot must disclose that the publisher's data vintage is unstated")
    map_hash = _valid_sha256(snapshot.get("map_page_sha256"), "map_page_sha256")
    methodology_hash = _valid_sha256(snapshot.get("methodology_page_sha256"), "methodology_page_sha256")
    if map_hash != _BARC_MAP_CAPTURE_SHA256:
        raise SourcePolicyError("map_page_sha256 does not match the pinned BARC capture")
    if methodology_hash != _BARC_METHOD_CAPTURE_SHA256:
        raise SourcePolicyError("methodology_page_sha256 does not match the pinned BARC capture")

    raw_areas = snapshot.get("area_hectares")
    if not isinstance(raw_areas, Mapping):
        raise SourcePolicyError("area_hectares must be an object")
    areas: dict[str, int] = {}
    for key in (*_SUITABILITY_CLASSES, "total"):
        value = raw_areas.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SourcePolicyError(f"area_hectares.{key} must be a nonnegative integer")
        areas[key] = value
    if areas["total"] <= 0 or sum(areas[key] for key in _SUITABILITY_CLASSES) != areas["total"]:
        raise SourcePolicyError("suitability-class areas must add up to the total area")
    if areas != _BARC_AREA_HECTARES:
        raise SourcePolicyError("suitability-class areas do not match the pinned BARC snapshot")
    _validate_page_extract(snapshot, areas)
    snapshot_digest = _valid_sha256(snapshot.get("snapshot_sha256"), "snapshot_sha256")
    if snapshot_digest != _snapshot_sha256(snapshot):
        raise SourcePolicyError("snapshot payload hash does not match its extracted values")

    return {
        "publisher": publisher,
        "crop_name": "Potato",
        "barc_crop_id": barc_crop_id,
        "country_code": country_code,
        "district": "Comilla",
        "upazila": "Comilla",
        "barc_upazila_id": barc_upazila_id,
        "retrieved_on": retrieved_on,
        "dataset_vintage": None,
        "source_url": source_url,
        "methodology_url": methodology_url,
        "license_url": license_url,
        "license": license,
        "map_page_sha256": map_hash,
        "methodology_page_sha256": methodology_hash,
        "area_hectares": areas,
        "snapshot_sha256": snapshot_digest,
        "page_extract": dict(snapshot["page_extract"]),
    }


def build_barc_knowledge_record(
    snapshot: Mapping[str, Any], crop_id: UUID, *, evaluated_on: date
) -> AgriculturalKnowledge:
    """Build an auto-accepted, upazila-level record without inventing a reviewer."""
    validated_snapshot = validate_barc_upazila_snapshot(snapshot, evaluated_on=evaluated_on)
    areas = validated_snapshot["area_hectares"]
    suitable_area, share = _suitable_area_and_share(validated_snapshot)
    applicability = {
        "country_code": validated_snapshot["country_code"],
        "district": validated_snapshot["district"],
        "upazila": validated_snapshot["upazila"],
    }
    content = {
        "source_type": "government_research_portal",
        "factor": "regional_crop_zoning",
        "evidence_type": "upazila_aggregated_suitability_area",
        "evidence_role": "regional_context_only",
        "applicability": applicability,
        "context": {
            "crop_name": validated_snapshot["crop_name"],
            "country_code": validated_snapshot["country_code"],
            "district": validated_snapshot["district"],
            "upazila": validated_snapshot["upazila"],
            "spatial_resolution": "upazila",
            "dataset_vintage": None,
        },
        "evidence": {
            "area_hectares_by_class": areas,
            "suitable_or_better_area_hectares": suitable_area,
            "suitable_or_better_share_percent": share,
            "dataset_vintage": None,
            "retrieved_on": validated_snapshot["retrieved_on"].isoformat(),
            "map_page_sha256": validated_snapshot["map_page_sha256"],
            "methodology_page_sha256": validated_snapshot["methodology_page_sha256"],
            "snapshot_sha256": validated_snapshot["snapshot_sha256"],
            "source_snapshot": dict(snapshot),
            "methodology_url": validated_snapshot["methodology_url"],
            "license_url": validated_snapshot["license_url"],
            "license": validated_snapshot["license"],
        },
        "factors": {"regional_crop_zoning": _regional_zoning_factor(validated_snapshot)},
        "acceptance_policy": {
            "id": BARC_POLICY_ID,
            "version": 1,
            "method": "automated_source_validation",
            "evaluated_on": evaluated_on.isoformat(),
            "retrieved_on": validated_snapshot["retrieved_on"].isoformat(),
            "checks_passed": sorted(_REQUIRED_CHECKS),
            "limitations": list(_POLICY_LIMITATIONS),
        },
    }
    return AgriculturalKnowledge(
        id=uuid4(),
        crop_id=crop_id,
        crop_variety_id=None,
        category="crop_suitability",
        region_code=validated_snapshot["upazila"],
        content=content,
        source_name=_BARC_SOURCE_NAME,
        source_reference=validated_snapshot["source_url"],
        effective_from=validated_snapshot["retrieved_on"],
        effective_to=validated_snapshot["retrieved_on"] + timedelta(days=BARC_REFRESH_DAYS),
        review_status="approved",
        reviewed_by=None,
        reviewed_at=None,
    )


def is_valid_automated_acceptance(
    row: Any, content: Mapping[str, Any], *, crop_name: str | None = None
) -> bool:
    """Validate the auditable source-policy markers before allowing reviewerless rows."""
    policy = content.get("acceptance_policy")
    if isinstance(policy, Mapping) and policy.get("id") in PORTAL_POLICY_IDS:
        return is_valid_portal_acceptance(row, content, crop_name=crop_name)
    evidence = content.get("evidence")
    context = content.get("context")
    snapshot = evidence.get("source_snapshot") if isinstance(evidence, Mapping) else None
    if not isinstance(policy, Mapping) or not isinstance(evidence, Mapping) or not isinstance(context, Mapping):
        return False
    if (
        policy.get("id") != BARC_POLICY_ID
        or policy.get("version") != 1
        or policy.get("method") != "automated_source_validation"
        or row.review_status != "approved"
        or row.reviewed_by is not None
        or row.reviewed_at is not None
        or row.crop_id is None
        or row.crop_variety_id is not None
        or row.category != "crop_suitability"
        or row.region_code != "Comilla"
        or row.source_name != _BARC_SOURCE_NAME
        or not isinstance(crop_name, str)
        or crop_name.casefold() != "potato"
        or content.get("source_type") != "government_research_portal"
        or content.get("factor") != "regional_crop_zoning"
        or content.get("evidence_type") != "upazila_aggregated_suitability_area"
        or content.get("evidence_role") != "regional_context_only"
        or context.get("crop_name") != "Potato"
        or context.get("district") != "Comilla"
        or context.get("upazila") != "Comilla"
        or context.get("country_code") != "BD"
        or context.get("spatial_resolution") != "upazila"
    ):
        return False
    expected_source = "https://apps.barc.gov.bd/cropzoning/homes/upazila/12/195"
    if row.source_reference != expected_source or not isinstance(snapshot, Mapping):
        return False
    if not _required_checks_present(policy.get("checks_passed")):
        return False
    if row.effective_from != _safe_iso_date(policy.get("retrieved_on")):
        return False
    expected_expiry = row.effective_from + timedelta(days=BARC_REFRESH_DAYS) if row.effective_from else None
    if row.effective_to != expected_expiry:
        return False
    evaluated_on = _safe_iso_date(policy.get("evaluated_on"))
    if evaluated_on is None:
        return False
    try:
        normalized_snapshot = validate_barc_upazila_snapshot(snapshot, evaluated_on=evaluated_on)
    except SourcePolicyError:
        return False
    if (
        normalized_snapshot["source_url"] != row.source_reference
        or normalized_snapshot["snapshot_sha256"] != evidence.get("snapshot_sha256")
        or not _same_json_value(normalized_snapshot["area_hectares"], evidence.get("area_hectares_by_class"))
        or evidence.get("map_page_sha256") != normalized_snapshot["map_page_sha256"]
        or evidence.get("methodology_page_sha256") != normalized_snapshot["methodology_page_sha256"]
        or evidence.get("retrieved_on") != normalized_snapshot["retrieved_on"].isoformat()
        or evidence.get("dataset_vintage") is not None
        or evidence.get("methodology_url") != normalized_snapshot["methodology_url"]
        or evidence.get("license_url") != normalized_snapshot["license_url"]
        or evidence.get("license") != normalized_snapshot["license"]
        or not _same_json_value(
            context,
            {
                "crop_name": normalized_snapshot["crop_name"],
                "country_code": normalized_snapshot["country_code"],
                "district": normalized_snapshot["district"],
                "upazila": normalized_snapshot["upazila"],
                "spatial_resolution": "upazila",
                "dataset_vintage": None,
            },
        )
        or not _same_json_value(
            content.get("applicability"),
            {
                "country_code": normalized_snapshot["country_code"],
                "district": normalized_snapshot["district"],
                "upazila": normalized_snapshot["upazila"],
            },
        )
        or not _same_json_value(
            content.get("factors"),
            {"regional_crop_zoning": _regional_zoning_factor(normalized_snapshot)},
        )
        or not _same_json_value(policy.get("limitations"), _POLICY_LIMITATIONS)
    ):
        return False
    try:
        suitable_area, expected_share = _suitable_area_and_share(normalized_snapshot)
    except (KeyError, TypeError, ZeroDivisionError):
        return False
    return (
        evidence.get("suitable_or_better_area_hectares") == suitable_area
        and evidence.get("suitable_or_better_share_percent") == expected_share
    )


def acceptance_method_for(
    row: Any, content: Mapping[str, Any], *, crop_name: str | None = None
) -> str | None:
    if is_valid_automated_acceptance(row, content, crop_name=crop_name):
        return portal_acceptance_method(content) or f"automated_source_policy:{BARC_POLICY_ID}:v1"
    if row.review_status == "approved" and row.reviewed_by is not None:
        return "human_review"
    return None


def _required_checks_present(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(check, str) for check in value)
        and _REQUIRED_CHECKS.issubset(value)
    )


def _safe_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
