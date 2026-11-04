from datetime import date, timedelta
import json

from app.core.auth import get_current_farmer_id


def test_public_advisory_validates_district_and_never_fetches_on_cache_miss(client_and_farm, monkeypatch, tmp_path):
    from app.api import routes_m2_advisor
    from app.services.climate import power_history
    client, _, _, _ = client_and_farm
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(power_history, "_request_power", lambda *_: (_ for _ in ()).throw(AssertionError("public route must not fetch")))
    assert client.get("/advisory", params={"district": "not-a-district", "crop": "rice", "season": "aman"}).status_code == 422
    response = client.get("/advisory", params={"district": "Rajshahi", "crop": "rice", "season": "aman"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "climate_cache_unavailable"


def test_public_advisory_reads_district_cache_without_private_farm_context(client_and_farm, monkeypatch, tmp_path):
    from app.api import routes_m2_advisor
    client, _, _, _ = client_and_farm
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    observations = []
    for year in range(2001, 2026):
        start = date(year, 1, 1)
        for offset in range((date(year + 1, 1, 1) - start).days):
            day = start + timedelta(days=offset)
            onset = date(year, 6, 1) + timedelta(days=10 if year <= 2012 else 20)
            observations.append({"date": str(day), "rainfall_mm": 4 if day >= onset else 0,
                                 "temperature_c": 25, "solar_mj_m2_day": 15})
    bundle = {
        "contract_version": "1.0.0",
        "manifest": {
            "contract_version": "1.0.0", "district_code": "5081", "bundle_id": "TEST ONLY",
            "created_at": "2026-11-01T00:00:00Z", "coverage_start": "2001-01-01",
            "coverage_end": "2025-12-31", "assets": [], "provenance": [{
                "source_id": "test-power", "source_name": "TEST ONLY NASA fixture",
                "source_url": "https://power.larc.nasa.gov/", "method": "nasa_power",
                "retrieved_at": "2026-11-01T00:00:00Z", "recorded_at": "2026-11-01T00:00:00Z",
                "quality_status": "verified", "spatial_resolution_m": 50000,
            }],
            "sampling_point": {"latitude": 24.37, "longitude": 88.60,
                               "description": "TEST ONLY representative point; not district mean",
                               "source_url": "https://example.invalid/test-point"},
        },
        "daily_series": observations,
    }
    directory = tmp_path / "5081"
    directory.mkdir()
    (directory / "bundle.json").write_text(json.dumps(bundle))
    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.get("/advisory", params={"district": "5081", "crop": "rice", "season": "aman"})
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "provisional"
    assert body["annual_comparison"]["observed_shift_days"] == 10
    assert body["recommended_shift_days"] is None
    assert body["gdd_summary"] is None
    assert body["calendar_references"]
    assert body["data_provenance"]["cache_status"] == "hit"
    assert body["definition_review_status"] == "exploratory_pending_review"
    assert "farmland_id" not in body and "season_id" not in body
    assert len(body["sms_bn"]) < 160 and len(body["sms_en"]) < 160
    bundle["manifest"]["provenance"][0]["quality_status"] = "stale"
    (directory / "bundle.json").write_text(json.dumps(bundle))
    stale = client.get("/advisory", params={"district": "5081", "crop": "rice", "season": "aman"})
    assert stale.status_code == 503


def test_public_advisory_returns_season_choices_without_guessing(client_and_farm):
    client, _, _, _ = client_and_farm
    response = client.get("/advisory", params={"district": "5081", "crop": "rice"})
    assert response.status_code == 200
    assert response.json()["status"] == "needs_selection"
    assert set(response.json()["season_choices"]) == {"aman", "aus", "boro"}


def test_public_advisory_does_not_apply_aman_onset_definition_to_other_rice_seasons(
    client_and_farm, monkeypatch, tmp_path
):
    from app.api import routes_m2_advisor
    from app.services import district_advisory

    client, _, _, _ = client_and_farm
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        district_advisory,
        "load_district_climate_evidence",
        lambda *_: (_ for _ in ()).throw(AssertionError("unsupported seasons must not reuse Aman onset")),
    )

    for season in ("aus", "boro"):
        response = client.get(
            "/advisory", params={"district": "Rajshahi", "crop": "rice", "season": season}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "insufficient_data"
        assert body["season"] == season
        assert body["annual_comparison"] is None
        assert body["recommended_shift_days"] is None
        assert body["gdd_summary"] is None
        assert body["calendar_references"]
        assert "monsoon" in body["message_en"].lower() or "rainfall" in body["message_en"].lower()
