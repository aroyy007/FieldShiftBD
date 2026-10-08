"""Automated acceptance rules for BARC Agri-Advisory Portal evidence.

These tests use the real pinned captures. Altered claims, captures, and rows
are built in memory only; nothing here is production data.
"""

import copy
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.services import m2_portal_policy as policy
from app.services import source_captures
from app.services.m2_source_policy import acceptance_method_for, is_valid_automated_acceptance

EVALUATED_ON = date(2026, 10, 8)
CROP_ID = uuid4()


def _claim(claim_id):
    return copy.deepcopy(next(c for c in policy.claims_manifest()["claims"] if c["claim_id"] == claim_id))


def test_every_manifest_claim_passes_the_bilingual_policy():
    for claim in policy.claims_manifest()["claims"]:
        content, provenance = policy.build_bilingual_content(claim, EVALUATED_ON)
        assert content["acceptance_policy"]["method"] == "automated_source_validation"
        assert provenance["sha256"] == source_captures.capture_entry(claim["capture"])["sha256"]


def test_detection_matches_both_language_versions_only():
    potato = source_captures.read_verified_json("portal/prod_tech_36.json")
    assert policy.corroborated_soil_textures(potato["land_and_soil"], potato["land_and_soil_bn"]) == {"loam"}
    maize = source_captures.read_verified_json("portal/prod_tech_5.json")
    # English names sandy loam (and excludes sandy/heavy clay); Bangla names loam and clay loam.
    assert policy.corroborated_soil_textures(maize["land_and_soil"], maize["land_and_soil_bn"]) == set()


def test_negated_sentences_do_not_count_as_support():
    assert policy.corroborated_soil_textures("All soils except clay are suitable.", "এটেল মাটি উপযোগী।") == set()


@pytest.mark.parametrize(
    ("claim_id", "dimension", "value"),
    [
        ("potato-land-soil-v1", "soil_texture", "sandy_loam"),  # English only
        ("potato-land-soil-v1", "soil_texture", "clay_loam"),  # Bangla only
        ("wheat-land-soil-v1", "land_type", "low"),  # in neither
    ],
)
def test_single_language_or_absent_values_are_rejected(claim_id, dimension, value):
    claim = _claim(claim_id)
    claim["values"][dimension].append(value)
    with pytest.raises(policy.PortalPolicyError):
        policy.build_bilingual_content(claim, EVALUATED_ON)


def test_harvest_period_months_must_appear_in_both_languages():
    claim = _claim("maize-harvest-calendar-v1")
    claim["values"]["periods"][1]["months"] = [5]
    with pytest.raises(policy.PortalPolicyError):
        policy.build_bilingual_content(claim, EVALUATED_ON)


@pytest.mark.parametrize("evaluated_on", [date(2026, 10, 7), date(2027, 4, 7)])
def test_future_dated_and_stale_captures_are_rejected(evaluated_on):
    with pytest.raises(policy.PortalPolicyError):
        policy.build_bilingual_content(_claim("potato-land-soil-v1"), evaluated_on)


def test_altered_capture_bytes_are_rejected(monkeypatch, tmp_path):
    target = tmp_path / "portal" / "prod_tech_36.json"
    target.parent.mkdir(parents=True)
    original = (source_captures.CAPTURE_ROOT / "portal" / "prod_tech_36.json").read_bytes()
    target.write_bytes(original.replace(b"Medium high", b"Medium hihg"))
    monkeypatch.setattr(source_captures, "CAPTURE_ROOT", tmp_path)
    source_captures.read_verified_bytes.cache_clear()
    try:
        with pytest.raises(source_captures.SourceCaptureError):
            source_captures.read_verified_bytes("portal/prod_tech_36.json")
        with pytest.raises(source_captures.SourceCaptureError):
            source_captures.read_verified_bytes("portal/not_in_manifest.json")
    finally:
        source_captures.read_verified_bytes.cache_clear()


def test_variety_durations_require_plausible_ranges_and_direct_planting():
    content = policy.build_variety_content("potato", 509, EVALUATED_ON)
    assert content["harvest_window_days_after_planting"] == {"min": 90, "max": 95}
    with pytest.raises(policy.PortalPolicyError):
        policy.build_variety_content("maize", 101, EVALUATED_ON)  # portal lists 10-150 days
    with pytest.raises(policy.PortalPolicyError):
        policy.build_variety_content("potato", 506, EVALUATED_ON)  # no duration published
    with pytest.raises(policy.PortalPolicyError):
        policy.build_variety_content("rice", 142, EVALUATED_ON)  # duration basis unstated
    with pytest.raises(policy.PortalPolicyError):
        policy.build_variety_content("wheat", 509, EVALUATED_ON)  # potato record, crop mismatch


def test_regional_context_has_no_positive_factor():
    record = policy.build_regional_record("potato", "201967", CROP_ID, EVALUATED_ON)
    assert record.content["evidence_role"] == "regional_context_only"
    assert "factors" not in record.content
    assert record.region_code == "BD-UPZ-201967"
    entry = record.content["evidence"]["entries"][0]
    assert round(sum(entry["class_shares_percent"].values())) == 100
    assert record.content["context"]["area_unit"] is None


def _valid_row():
    return policy.build_bilingual_record(_claim("potato-land-soil-v1"), CROP_ID, EVALUATED_ON)


def test_read_time_validation_accepts_untouched_rows():
    row = _valid_row()
    assert is_valid_automated_acceptance(row, row.content, crop_name="Potato")
    assert acceptance_method_for(row, row.content, crop_name="Potato") == (
        "automated_source_policy:m2-barc-portal-bilingual-v1:v1"
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.content["factors"]["land_and_soil"]["when"]["soil_texture"].append("sand"),
        lambda row: row.content["claim"]["values"]["land_type"].append("medium_high"),
        lambda row: row.content["factors"]["land_and_soil"].__setitem__("explanation", "Guaranteed yield."),
        lambda row: setattr(row, "effective_to", date(2099, 1, 1)),
        lambda row: setattr(row, "reviewed_by", uuid4()),
        lambda row: setattr(row, "reviewed_at", datetime.now(timezone.utc)),
        lambda row: setattr(row, "region_code", "BD-UPZ-201967"),
        lambda row: setattr(row, "review_status", "in_review"),
    ],
)
def test_read_time_validation_rejects_edited_rows(mutate):
    row = _valid_row()
    row.content = copy.deepcopy(row.content)
    mutate(row)
    assert not is_valid_automated_acceptance(row, row.content, crop_name="Potato")


def test_read_time_validation_rejects_crop_mismatch():
    row = _valid_row()
    assert not is_valid_automated_acceptance(row, row.content, crop_name="Wheat")
    assert not is_valid_automated_acceptance(row, row.content, crop_name=None)


def test_license_capture_is_checked():
    assert policy._LICENSE_SENTENCE in source_captures.read_verified_bytes("portal/copyright_policy.html").decode()
