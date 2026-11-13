from datetime import date, datetime, timezone
from uuid import uuid4


def _snapshot(**profile_changes):
    from app.contracts.challenge.v1 import FarmProfileSnapshot

    profile = {
        "country_code": "BD", "land_area_sqm": 1200, "area_unit": "square_metre",
        "district_code": "5081", "district": "Rajshahi", "soil_type": "clay",
        "land_type": "high", "irrigation_available": True,
    }
    profile.update(profile_changes)
    return FarmProfileSnapshot.model_validate({
        "contract_version": "1.0.0", "farmland_id": str(uuid4()), "farmer_id": str(uuid4()),
        "captured_at": datetime(2026, 11, 7, tzinfo=timezone.utc).isoformat(),
        "profile": profile,
        "provenance": [{"source_id": "farmer-profile", "source_name": "Farmer profile",
            "retrieved_at": "2026-11-07T00:00:00Z", "recorded_at": "2026-11-07T00:00:00Z",
            "method": "farmer_input"}],
        "rotation_history": [{"season_id": str(uuid4()), "crop_code": "rice", "planting_date": "2026-07-01", "source": "farmer_reported"}],
    })


def test_catalog_preserves_incomplete_baseline_and_unreviewed_source_scope():
    from app.services.rotation.catalog import load_rotation_candidates

    candidates = load_rotation_candidates("5081", _snapshot())
    baseline = next(candidate for candidate in candidates if candidate.role == "baseline")
    assert len(baseline.steps) == 1
    assert baseline.steps[0].start_date == date(2026, 7, 1)
    assert baseline.steps[0].end_date is None
    assert baseline.applicability == "unknown"
    alternatives = [candidate for candidate in candidates if candidate.role == "alternative"]
    assert alternatives
    assert all(candidate.source_ids for candidate in alternatives)
    assert all(candidate.review_status == "source_verified_pending_agronomy_review" for candidate in alternatives)
    assert all(candidate.applicability == "unknown" for candidate in alternatives)


def test_known_profile_conflict_is_ineligible_but_missing_profile_facts_stay_unknown():
    from app.services.rotation.catalog import load_rotation_candidates

    conflict = load_rotation_candidates("2015", _snapshot(district_code="2015", district="Chattogram", land_type="low"))
    conflict_options = [c for c in conflict if c.role == "alternative"]
    assert conflict_options and all(c.applicability == "ineligible" for c in conflict_options)
    incomplete = load_rotation_candidates("2015", _snapshot(district_code="2015", district="Chattogram", land_type=None, soil_type=None, irrigation_available=None))
    incomplete_options = [c for c in incomplete if c.role == "alternative"]
    assert incomplete_options and all(c.applicability == "unknown" for c in incomplete_options)


def test_unsupported_region_is_rejected_instead_of_reusing_broad_pattern():
    import pytest
    from app.services.rotation.catalog import load_rotation_candidates

    with pytest.raises(ValueError, match="supported regional comparison"):
        load_rotation_candidates("9999", _snapshot())


def test_wet_seeded_aman_does_not_receive_transplanted_variety_dates():
    from app.services.rotation.catalog import load_rotation_candidates

    candidates = load_rotation_candidates("2015", _snapshot(district_code="2015", district="Chattogram"))
    published = next(candidate for candidate in candidates if candidate.candidate_id == "BRRI-RFS-02")
    aman = next(step for step in published.steps if step.season_code == "aman")
    assert aman.cultivation_method == "wet_seeded"
    assert "BRRI dhan33" in aman.variety_names
    assert aman.window is None
    assert "brri-riceprofile-variety-44" not in aman.source_ids
    assert aman.gdd_target is None


def test_bangla_profile_aliases_use_shared_m1_vocabulary_without_guessing_unknown_text():
    from app.services.rotation.catalog import load_rotation_candidates

    known_alias = load_rotation_candidates("5081", _snapshot(land_type="উঁচু জমি", soil_type="এঁটেল দোআঁশ"))
    known_alternatives = [c for c in known_alias if c.role == "alternative"]
    assert known_alternatives and all(c.applicability == "unknown" for c in known_alternatives)
    unknown_alias = load_rotation_candidates("5081", _snapshot(soil_type="soil phrase not in vocabulary"))
    unknown_alternatives = [c for c in unknown_alias if c.role == "alternative"]
    assert unknown_alternatives and all(c.applicability == "unknown" for c in unknown_alternatives)


def test_region_argument_cannot_override_a_different_profile_district():
    import pytest
    from app.services.rotation.catalog import load_rotation_candidates

    with pytest.raises(ValueError, match="does not match the farm profile"):
        load_rotation_candidates("2015", _snapshot())
