"""Authenticated crop-calendar gating for the NASA farmer advisory."""

from datetime import date, datetime, timedelta, timezone
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.core import AgriculturalKnowledge, Farmland
from app.models.season import Season
from app.contracts.challenge.v1 import ClimateVariableCoverage, DailyClimateObservation
from app.services.rotation_comparison import BrriRotationComparisonProvider


@pytest.fixture
def rotation_client_and_farm(client_and_farm, monkeypatch):
    client, farmland_id, season_id, stage_id = client_and_farm
    runtime = client.app.state.challenge_runtime
    monkeypatch.setattr(runtime, "switches", replace(runtime.switches, rotation=True))
    monkeypatch.setitem(runtime.adapters, "rotation", BrriRotationComparisonProvider())
    return client, farmland_id, season_id, stage_id


def test_planting_window_reports_observed_shift_without_turning_it_into_advice(
    client_and_farm, monkeypatch
):
    client, farmland_id, season_id, _ = client_and_farm
    db_dependency = client.app.dependency_overrides[get_db]()
    db = next(db_dependency)
    farmer_id = client.app.dependency_overrides[get_current_farmer_id]()
    season = db.get(Season, season_id)
    farmland = db.get(Farmland, farmland_id)
    farmland.division = "Chattogram"
    farmland.district = "Comilla"
    farmland.latitude = 23.46
    farmland.longitude = 91.18
    db.add(AgriculturalKnowledge(
        crop_id=season.crop_id,
        category="crop_calendar",
        region_code=None,
        content={
            "planting_window": {
                "season_start_month": 6,
                "season_start_day": 1,
                "season_end_month": 10,
                "season_end_day": 31,
            },
            "gdd": {"base_temperature_c": 10, "cap_temperature_c": 30},
        },
        source_name="TEST ONLY reviewed calendar",
        source_reference="https://example.invalid/test-calendar",
        review_status="approved",
        reviewed_by=farmer_id,
        reviewed_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db_dependency.close()

    observations = []
    for year in range(2001, 2026):
        season_start = date(year, 6, 1)
        onset_offset = 50 if year <= 2012 else 60
        days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
        for offset in range(days_in_year):
            observation_date = date(year, 1, 1) + timedelta(days=offset)
            season_offset = (observation_date - season_start).days
            observations.append(DailyClimateObservation(
                date=observation_date,
                rainfall_mm=(
                    4 if 0 <= season_offset < 153 and season_offset >= onset_offset else 0
                ),
                temperature_c=25,
                solar_mj_m2_day=15,
            ))

    coverage = [
        ClimateVariableCoverage(
            variable=variable,
            units=units,
            status="available",
            expected_observations=9131,
            valid_observations=9131,
            missing_observations=0,
        )
        for variable, units in (
            ("rainfall_mm", "mm/day"),
            ("temperature_c", "°C"),
            ("solar_mj_m2_day", "MJ/m²/day"),
        )
    ]
    bundle = SimpleNamespace(
        daily_series=observations,
        manifest=SimpleNamespace(
            coverage_start=date(2001, 1, 1),
            coverage_end=date(2025, 12, 31),
            created_at=datetime.now(timezone.utc),
            coverage_by_variable=coverage,
        ),
    )

    class StubPowerHistoryProvider:
        def __init__(self, *_args):
            pass

        def has_cached_bundle(self, *_args):
            return True

        def get_bundle(self, *_args, **_kwargs):
            return bundle

    monkeypatch.setattr(
        "app.api.routes_m2_advisor.NasaPowerHistoryProvider",
        StubPowerHistoryProvider,
    )

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["annual_comparison"]["observed_shift_days"] == 10
    assert body["recommended_shift_days"] is None
    assert body["gdd_summary"]["baseline_valid_years"] == 12
    assert body["gdd_summary"]["recent_valid_years"] == 13
    assert body["data_provenance"]["cache_status"] == "hit"


def test_planting_window_reports_insufficient_data_without_reviewed_calendar(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert "calendar" in body["message_en"]
    assert body["annual_comparison"] is None
    assert body["gdd_summary"] is None
    assert body["variety_calendar_reference"] is None
    assert body["data_provenance"]["source"] == "NASA POWER Daily Point"
    assert body["data_provenance"]["spatial_resolution_m"] == 50000
    assert body["data_provenance"]["cache_status"] == "not_requested"


def test_planting_window_handles_reviewed_generic_calendar_without_coordinates(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    db_dependency = client.app.dependency_overrides[get_db]()
    db = next(db_dependency)
    farmer_id = client.app.dependency_overrides[get_current_farmer_id]()
    season = db.get(Season, season_id)
    farmland = db.get(Farmland, farmland_id)
    farmland.division = "Chattogram"
    farmland.district = "Comilla"
    db.add(AgriculturalKnowledge(
        crop_id=season.crop_id,
        category="crop_calendar",
        region_code=None,
        content={
            "planting_window": {
                "season_start_month": 6,
                "season_start_day": 1,
                "season_end_month": 10,
                "season_end_day": 31,
            },
            "gdd": {"base_temperature_c": 10, "cap_temperature_c": 30},
        },
        source_name="TEST ONLY reviewed calendar",
        source_reference="https://example.invalid/test-calendar",
        review_status="approved",
        reviewed_by=farmer_id,
        reviewed_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db_dependency.close()

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert "location" in body["message_en"]
    assert body["planting_calendar"]["source_name"] == "TEST ONLY reviewed calendar"


def test_planting_window_returns_brri_variety_reference_without_turning_it_into_advice(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    db_dependency = client.app.dependency_overrides[get_db]()
    db = next(db_dependency)
    db.get(Season, season_id).variety_name = "BRRI dhan80"
    db.commit()
    db_dependency.close()

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 200
    body = response.json()
    reference = body["variety_calendar_reference"]
    assert body["status"] == "insufficient_data"
    assert body["recommended_shift_days"] is None
    assert reference["variety_name"] == "BRRI dhan80"
    assert reference["transplanting_window"] == {"start": "07-30", "end": "08-20"}
    assert reference["source_url"] == "https://riceprofile.brri.gov.bd/varieties/90"


def test_planting_window_hides_other_farmers_seasons(client_and_farm):
    client, _, season_id, _ = client_and_farm
    other_farmland_id = client.app.state.other_farmland_id

    response = client.get(
        f"/advisor/farmlands/{other_farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 404


def test_planting_window_requires_authentication(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.get(
            f"/advisor/farmlands/{farmland_id}/planting-window",
            params={"season_id": str(season_id)},
        )
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override

    assert response.status_code == 401


def test_rotation_comparison_returns_only_patterns_matching_documented_farm_scope(
    rotation_client_and_farm,
):
    client, farmland_id, _season_id, _ = rotation_client_and_farm
    db_dependency = client.app.dependency_overrides[get_db]()
    db = next(db_dependency)
    farmland = db.get(Farmland, farmland_id)
    farmland.land_type = "high"
    farmland.soil_type = "clay loam"
    farmland.irrigation_available = True
    db.commit()
    db_dependency.close()

    profile_update = client.patch(
        f"/farmlands/{farmland_id}", json={"previous_crop": "Mustard"}
    )
    assert profile_update.status_code == 200, profile_update.text
    assert profile_update.json()["previous_crop"] == "Mustard"

    response = client.post(
        f"/advisor/farmlands/{farmland_id}/rotation-comparisons"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert len(body["alternatives"]) == 2
    assert all(item["applicability_status"] == "matches_documented_scope"
               for item in body["strategies"])
    assert body["farmer_reported_previous_crop"] == "Mustard"
    assert body["selection_allowed"] is False
    assert any("NASA" in item for item in body["not_assessed_en"])
    assert body["evidence"][0]["source_url"] == (
        "https://brri.gov.bd/pages/static-pages/6922dc9b933eb65569e1140d"
    )
    assert body["evidence"][0]["retrieved_at"].startswith("2026-11-01T00:00:00")
    assert body["evidence"][0]["recorded_at"] == body["evidence"][0]["retrieved_at"]
    assert all(item["calendar_feasibility_status"] == "insufficient_reviewed_evidence"
               for item in body["strategies"])
    green_manure_pattern = next(item for item in body["strategies"] if item["strategy_id"] == "BRRI-RFS-04")
    aman = next(item for item in green_manure_pattern["steps"] if item["season_code"] == "aman")
    assert aman["cultivation_method"] == "transplanted"
    assert aman["calendar_evidence"]["status"] == "source_reference_available"
    assert aman["calendar_evidence"]["references"][0]["variety_name"] == "BRRI dhan31"
    assert aman["calendar_evidence"]["references"][0]["activation_allowed"] is False
    boro = next(item for item in green_manure_pattern["steps"] if item["season_code"] == "boro")
    assert boro["cultivation_method"] == "wet_seeded"
    assert boro["calendar_evidence"]["status"] != "source_reference_available"


def test_rotation_comparison_explains_scope_mismatch_without_suggesting_patterns(
    rotation_client_and_farm,
):
    client, farmland_id, _season_id, _ = rotation_client_and_farm
    db_dependency = client.app.dependency_overrides[get_db]()
    db = next(db_dependency)
    farmland = db.get(Farmland, farmland_id)
    farmland.land_type = "high"
    farmland.soil_type = "clay loam"
    farmland.irrigation_available = False
    db.commit()
    db_dependency.close()

    response = client.post(
        f"/advisor/farmlands/{farmland_id}/rotation-comparisons"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "outside_documented_scope"
    assert body["alternatives"] == []
    assert body["selection_allowed"] is False
    assert any("irrigation" in item.lower() for item in body["scope_notes_en"])


def test_rotation_comparison_returns_missing_farm_conditions_as_unknowns(rotation_client_and_farm):
    client, farmland_id, _season_id, _ = rotation_client_and_farm

    response = client.post(
        f"/advisor/farmlands/{farmland_id}/rotation-comparisons"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_evidence"
    assert body["alternatives"] == []
    assert body["selection_allowed"] is False
    assert len(body["unknowns_en"]) == 3


def test_rotation_comparison_requires_farmland_ownership_and_auth(rotation_client_and_farm):
    client, farmland_id, _season_id, _ = rotation_client_and_farm
    other_farmland_id = client.app.state.other_farmland_id
    response = client.post(
        f"/advisor/farmlands/{other_farmland_id}/rotation-comparisons"
    )
    assert response.status_code == 404

    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.post(
            f"/advisor/farmlands/{farmland_id}/rotation-comparisons"
        )
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override
    assert response.status_code == 401
