"""M1 catalog + M2 knowledge ingestion and the M1 → M2 API flow with real evidence.

The knowledge comes from the pinned BARC captures through the real importer.
Farmers, farmlands, and conflicting rows below are generated test fixtures in
an isolated SQLite database (TEST ONLY); no synthetic agronomic claim is added.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.main import app
from app.models import AgriculturalKnowledge, Base, Crop, CropVariety, Farmer, Farmland
from app.services import m2_advisor
from app.services.m1_catalog_import import crop_row_id, import_crop_catalog
from app.services.m2_portal_policy import BILINGUAL_POLICY_ID, knowledge_row_id
from app.services.m2_source_import import import_barc_snapshot, import_portal_knowledge

import json
from pathlib import Path

EVALUATED_ON = date(2026, 10, 8)
FARM_TODAY = date(2026, 10, 10)
SNAPSHOT = json.loads(
    (Path(__file__).resolve().parents[1] / "app/data/m2_knowledge_sources/barc_potato_comilla_snapshot.json").read_text(
        encoding="utf-8"
    )
)


def _engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    saved = []
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is None:
                continue
            default_sql = str(column.server_default.arg)
            if "gen_random_uuid" in default_sql or "::jsonb" in default_sql:
                saved.append((column, column.server_default))
                column.server_default = None
    Base.metadata.create_all(engine)
    return engine, saved


@pytest.fixture
def db():
    engine, saved = _engine()
    session = sessionmaker(autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        for column, default in saved:
            column.server_default = default
        engine.dispose()


def run_full_import(session):
    catalog = import_crop_catalog(session)
    import_barc_snapshot(session, SNAPSHOT, evaluated_on=EVALUATED_ON, crop_id=catalog.crop_ids["potato"])
    knowledge = import_portal_knowledge(session, catalog.crop_ids, evaluated_on=EVALUATED_ON)
    session.commit()
    return catalog, knowledge


# ── Ingestion ────────────────────────────────────────────────────────────────

def test_ingestion_twice_is_idempotent_with_stable_ids(db):
    first_catalog, first = run_full_import(db)
    ids_before = {row.id: (row.crop_id, row.crop_variety_id) for row in db.scalars(select(AgriculturalKnowledge))}
    second_catalog, second = run_full_import(db)
    ids_after = {row.id: (row.crop_id, row.crop_variety_id) for row in db.scalars(select(AgriculturalKnowledge))}

    assert first_catalog.crops_created == 4 and second_catalog.crops_unchanged == 4
    assert second_catalog.varieties_created == 0 and second_catalog.varieties_unchanged == first_catalog.varieties_created
    assert first.created == 308 and first.conflicts == []
    assert second.created == second.refreshed == 0 and second.unchanged == 308
    assert ids_before == ids_after
    assert first_catalog.crop_ids == second_catalog.crop_ids
    assert first_catalog.crop_ids["potato"] == crop_row_id("potato")
    assert len(first.rejected) == 5  # portal variety records without a plausible duration


def test_existing_teammate_crop_is_bound_by_alias_and_preserved(db):
    teammate = Crop(id=uuid4(), name="Corn", scientific_name=None, description="teammate row")
    db.add(teammate)
    db.commit()
    catalog, _ = run_full_import(db)

    assert catalog.crop_ids["maize"] == teammate.id
    db.refresh(teammate)
    assert (teammate.name, teammate.description) == ("Corn", "teammate row")
    assert db.scalar(select(func.count()).select_from(Crop).where(Crop.name == "Maize")) == 0
    assert db.scalar(select(func.count()).select_from(CropVariety).where(CropVariety.crop_id == teammate.id)) > 0
    assert any("bound to existing row 'Corn'" in note for note in catalog.notes)


def test_duplicate_catalog_rows_and_conflicting_values_are_reported_not_overwritten(db):
    db.add_all([
        Crop(id=uuid4(), name="Maize"), Crop(id=uuid4(), name="Corn"),
        Crop(id=uuid4(), name="Wheat", scientific_name="Triticum durum"),
        Crop(id=crop_row_id("rice"), name="Jute"),
    ])
    db.commit()
    catalog = import_crop_catalog(db)
    db.commit()

    joined = "\n".join(catalog.conflicts)
    assert "crop maize: several existing rows" in joined
    assert "crop wheat: existing row 'Wheat' has scientific name 'Triticum durum'" in joined
    assert "crop rice: deterministic id" in joined
    assert "maize" not in catalog.crop_ids and "rice" not in catalog.crop_ids
    assert db.scalar(select(Crop.scientific_name).where(Crop.name == "Wheat")) == "Triticum durum"
    assert db.get(Crop, crop_row_id("rice")).name == "Jute"


def test_human_reviewed_or_foreign_rows_are_never_overwritten(db):
    catalog = import_crop_catalog(db)
    reviewer = Farmer(id=uuid4(), name="TEST ONLY reviewer", phone_e164="+8801700009999")
    db.add(reviewer)
    db.flush()
    taken_id = knowledge_row_id(BILINGUAL_POLICY_ID, "potato-land-soil-v1")
    human = AgriculturalKnowledge(
        id=taken_id, crop_id=catalog.crop_ids["potato"], category="crop_suitability", region_code="BD",
        content={"source_type": "test_fixture", "note": "TEST ONLY human-reviewed row"},
        source_name="TEST ONLY", source_reference="test://human", review_status="approved",
        reviewed_by=reviewer.id, reviewed_at=datetime.now(timezone.utc),
    )
    duplicate_key = AgriculturalKnowledge(
        id=uuid4(), crop_id=catalog.crop_ids["wheat"], category="crop_suitability", region_code="BD",
        content={"source_type": "test_fixture"}, source_name="TEST ONLY",
        source_reference="https://portal.cropzoning.gov.bd/CropInfo/ProductionTechs?c=4",
        review_status="draft",
    )
    db.add_all([human, duplicate_key])
    db.commit()

    report = import_portal_knowledge(db, catalog.crop_ids, evaluated_on=EVALUATED_ON)
    db.commit()
    db.refresh(human)
    assert human.content["note"] == "TEST ONLY human-reviewed row"
    assert any("not owned by this policy" in item for item in report.conflicts)
    assert any("already covers" in item for item in report.conflicts)


def test_edited_policy_row_is_detected_and_restored_by_refresh(db):
    catalog, _ = run_full_import(db)
    row = db.get(AgriculturalKnowledge, knowledge_row_id(BILINGUAL_POLICY_ID, "potato-land-soil-v1"))
    content = json.loads(json.dumps(row.content))
    content["factors"]["land_and_soil"]["when"]["soil_texture"].append("sand")
    row.content = content
    db.commit()

    report = import_portal_knowledge(db, catalog.crop_ids, evaluated_on=EVALUATED_ON)
    db.commit()
    assert report.refreshed == 1
    db.refresh(row)
    assert row.content["factors"]["land_and_soil"]["when"]["soil_texture"] == ["loam"]


def test_missing_catalog_crop_rejects_dependent_knowledge(db):
    report = import_portal_knowledge(db, {}, evaluated_on=EVALUATED_ON)
    assert report.created == 0
    assert any("is not in the catalog" in item for item in report.rejected)


# ── API flow ─────────────────────────────────────────────────────────────────

class Api:
    def __init__(self, client, session):
        self.client = client
        self.db = session
        self.farmer_id = None

    def as_farmer(self, farmer_id):
        app.dependency_overrides[get_current_farmer_id] = lambda: farmer_id
        self.farmer_id = farmer_id

    def farmland(self, **fields):
        body = {"name": "TEST ONLY field", "land_area_sqm": 8093.71, "land_area_display_unit": "acre", **fields}
        response = self.client.post("/farmlands", json=body)
        assert response.status_code == 201, response.text
        return response.json()


@pytest.fixture
def api(db):
    run_full_import(db)
    farmer = Farmer(id=uuid4(), name="TEST ONLY farmer", phone_e164="+8801700001111")
    other = Farmer(id=uuid4(), name="TEST ONLY other", phone_e164="+8801700002222")
    db.add_all([farmer, other])
    db.commit()

    def override_get_db():
        yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    with patch.object(m2_advisor, "_farm_today", return_value=FARM_TODAY):
        with TestClient(app) as client:
            helper = Api(client, db)
            helper.other_farmer_id = other.id
            helper.as_farmer(farmer.id)
            yield helper
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def recommend(api, farmland_id):
    response = api.client.post(f"/advisor/farmlands/{farmland_id}/recommendations")
    assert response.status_code == 200, response.text
    return response.json()


def test_m1_profile_writes_are_canonicalized(api):
    farm = api.farmland(district="Comilla", upazila="adarsha sadar", soil_type="দো-আঁশ", land_type="উঁচু জমি")
    assert (farm["district"], farm["upazila"], farm["soil_type"], farm["land_type"]) == (
        "Cumilla", "Adarsha Sadar", "Loam", "high",
    )
    assert (farm["district_code"], farm["upazila_code"]) == ("2019", "201967")
    bad_division = api.client.patch(f"/farmlands/{farm['id']}", json={"division": "Sylhet"})
    assert bad_division.status_code == 422
    bad_land = api.client.patch(f"/farmlands/{farm['id']}", json={"land_type": "hilly"})
    assert bad_land.status_code == 422
    status = api.client.get(f"/farmlands/{farm['id']}/onboarding-status").json()
    assert "land_type" not in status["missing_fields"] and "upazila" not in status["missing_fields"]


def test_supported_profile_gets_evidence_backed_recommendations_and_regional_context(api):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="high")
    body = recommend(api, farm["id"])

    assert body["status"] == "available" and body["profile_source"] == "m1_saved_farmland"
    names = {item["crop"]["name"] for item in body["recommendations"]}
    assert names == {"Potato", "Wheat"}
    potato = next(item for item in body["recommendations"] if item["crop"]["name"] == "Potato")
    factor = potato["reasoning"]["positive_factors"][0]
    assert factor["factor"] == "land_and_soil"
    assert factor["knowledge_refs"][0]["acceptance_method"] == "automated_source_policy:m2-barc-portal-bilingual-v1:v1"
    assert factor["knowledge_refs"][0]["reviewed_by"] is None
    # Regional context is reported separately and never appears as a fit reason.
    regional_crops = {item["crop"]["name"] for item in body["regional_context"]}
    assert {"Potato", "Wheat", "Maize", "Rice"} <= regional_crops
    assert all(
        ref["category"] != "crop_suitability" or ref["region_code"] == "BD"
        for item in body["recommendations"] for ref in item["knowledge_refs"]
    )
    statuses = {item["crop"]["name"]: item["status"] for item in body["crop_assessments"]}
    assert statuses == {"Maize": "regional_context_only", "Potato": "supported_fit", "Rice": "regional_context_only", "Wheat": "supported_fit"}


def test_regional_context_alone_never_creates_a_recommendation(api):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="low")
    body = recommend(api, farm["id"])
    assert body["recommendations"] == []
    assert body["status"] == "no_supported_fit"
    assert body["regional_context"]
    assert {item["status"] for item in body["crop_assessments"]} <= {"conditions_not_met", "regional_context_only"}


def test_legacy_comilla_snapshot_stays_regional_context_only(api):
    farm = api.farmland(district="Comilla", upazila="Comilla", soil_type="Loam", land_type="low")
    db_row = api.db.scalar(select(AgriculturalKnowledge).where(AgriculturalKnowledge.region_code == "Comilla"))
    assert db_row is not None and db_row.content["evidence_role"] == "regional_context_only"
    body = recommend(api, farm["id"])
    assert body["recommendations"] == []


def test_missing_profile_fields_are_reported_instead_of_a_fit(api):
    farm = api.farmland(district="Gazipur", soil_type="Loam")
    body = recommend(api, farm["id"])
    assert body["status"] == "profile_incomplete"
    assert body["missing_profile_fields"] == ["land_type"]
    assert body["recommendations"] == []
    unknown_soil = api.farmland(district="Gazipur", soil_type="red earth", land_type="high")
    body = recommend(api, unknown_soil["id"])
    assert body["missing_profile_fields"] == ["soil_type"]


def test_request_body_cannot_override_the_saved_m1_profile(api):
    farm = api.farmland(district="Gazipur")
    response = api.client.post("/advisor/recommendations", json={
        "farmland_id": farm["id"], "soil_type": "Loam", "land_type": "high",
        "location": {"country_code": "BD", "district": "Gazipur"},
    })
    assert response.status_code == 200
    assert response.json()["recommendations"] == []
    assert response.json()["status"] == "profile_incomplete"


@pytest.mark.parametrize("today", [date(2026, 10, 1), date(2027, 4, 7)])
def test_future_and_expired_evidence_is_not_used(api, today):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="high")
    with patch.object(m2_advisor, "_farm_today", return_value=today):
        body = recommend(api, farm["id"])
    assert body["status"] == "no_approved_knowledge"
    assert body["recommendations"] == [] and body["regional_context"] == []


def test_tampered_database_row_is_ignored(api):
    row = api.db.get(AgriculturalKnowledge, knowledge_row_id(BILINGUAL_POLICY_ID, "potato-land-soil-v1"))
    content = json.loads(json.dumps(row.content))
    content["factors"]["land_and_soil"]["when"]["soil_texture"] = ["sand"]
    row.content = content
    api.db.commit()
    farm = api.farmland(district="Gazipur", soil_type="Sand", land_type="high")
    body = recommend(api, farm["id"])
    assert "Potato" not in {item["crop"]["name"] for item in body["recommendations"]}


def _catalog(api):
    crops = api.client.get("/crops").json()
    return {crop["name"]: crop for crop in crops}


def test_catalog_and_reference_endpoints(api):
    catalog = _catalog(api)
    assert set(catalog) == {"Maize", "Potato", "Rice", "Wheat"}
    assert any(v["name"] == "BARI Alu-7 (Diamant)" for v in catalog["Potato"]["varieties"])
    assert catalog["Maize"]["aliases"] and "corn" in catalog["Maize"]["aliases"]
    locations = api.client.get("/reference/locations").json()
    assert len(locations) == 8
    vocab = api.client.get("/reference/profile-vocabulary").json()
    assert {item["code"] for item in vocab["land_types"]} == {"high", "medium_high", "medium_low", "low", "very_low"}
    assert api.client.get(f"/crops/{uuid4()}").status_code == 404


def test_selection_harvest_window_and_missing_plan_evidence(api):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="high")
    body = recommend(api, farm["id"])
    potato = next(item for item in body["recommendations"] if item["crop"]["name"] == "Potato")
    variety = next(v for v in _catalog(api)["Potato"]["varieties"] if v["name"] == "BARI Alu-7 (Diamant)")
    season = api.client.post("/advisor/seasons", json={
        "farmland_id": farm["id"], "crop_id": potato["crop"]["crop_id"],
        "crop_variety_id": variety["crop_variety_id"], "variety_name": variety["name"],
        "recommendation_id": potato["recommendation_id"], "planting_date": "2026-11-20",
    })
    assert season.status_code == 201, season.text
    season_id = season.json()["season_id"]

    harvest = api.client.get(f"/advisor/seasons/{season_id}/harvest-guidance")
    assert harvest.status_code == 200, harvest.text
    guidance = harvest.json()
    assert (guidance["recommended_window_start"], guidance["recommended_window_end"]) == ("2027-02-18", "2027-02-23")
    assert guidance["knowledge_refs"][0]["acceptance_method"].startswith("automated_source_policy:m2-barc-portal-variety")

    plan = api.client.post(f"/advisor/seasons/{season_id}/plan", json={"season_id": season_id, "title": "Plan"})
    assert plan.status_code == 409
    assert "No approved season-plan knowledge" in plan.json()["detail"]
    activate = api.client.post(f"/advisor/seasons/{season_id}/activate")
    assert activate.status_code == 409
    assert api.client.get(f"/advisor/seasons/{season_id}/plan").status_code == 404
    seasons = api.client.get(f"/advisor/farmlands/{farm['id']}/seasons").json()
    assert seasons[0]["crop_variety_id"] == variety["crop_variety_id"]


def test_harvest_guidance_without_variety_and_for_uncovered_crops(api):
    catalog = _catalog(api)
    wheat_farm = api.farmland(district="Gazipur")
    season = api.client.post("/advisor/seasons", json={
        "farmland_id": wheat_farm["id"], "crop_id": catalog["Wheat"]["crop_id"],
    }).json()
    guidance = api.client.get(f"/advisor/seasons/{season['season_id']}/harvest-guidance").json()
    assert guidance["maturity_indicators"] == ["The crop turns a golden colour at full maturity."]
    assert guidance["recommended_window_start"] is None
    assert any("Select a variety" in note for note in guidance["uncertainty_notes"])

    maize_farm = api.farmland(district="Gazipur")
    maize = api.client.post("/advisor/seasons", json={
        "farmland_id": maize_farm["id"], "crop_id": catalog["Maize"]["crop_id"],
    }).json()
    maize_guidance = api.client.get(f"/advisor/seasons/{maize['season_id']}/harvest-guidance").json()
    assert any("Rabi-season maize" in item for item in maize_guidance["guidance"])

    rice_farm = api.farmland(district="Gazipur")
    rice = api.client.post("/advisor/seasons", json={
        "farmland_id": rice_farm["id"], "crop_id": catalog["Rice"]["crop_id"],
    }).json()
    assert api.client.get(f"/advisor/seasons/{rice['season_id']}/harvest-guidance").status_code == 409


def test_variety_must_belong_to_the_selected_crop(api):
    catalog = _catalog(api)
    farm = api.farmland(district="Gazipur")
    response = api.client.post("/advisor/seasons", json={
        "farmland_id": farm["id"], "crop_id": catalog["Potato"]["crop_id"],
        "crop_variety_id": catalog["Wheat"]["varieties"][0]["crop_variety_id"],
    })
    assert response.status_code == 422
    missing = api.client.post("/advisor/seasons", json={"farmland_id": farm["id"], "crop_id": str(uuid4())})
    assert missing.status_code == 404


def test_ownership_isolation_and_authentication(api):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="high")
    api.as_farmer(api.other_farmer_id)
    assert api.client.post(f"/advisor/farmlands/{farm['id']}/recommendations").status_code == 404
    assert api.client.post("/advisor/recommendations", json={"farmland_id": farm["id"]}).status_code == 404
    assert api.client.get(f"/advisor/farmlands/{farm['id']}/recommendations").status_code == 404
    app.dependency_overrides.pop(get_current_farmer_id)
    assert api.client.post(f"/advisor/farmlands/{farm['id']}/recommendations").status_code == 401


def test_m3_state_and_m6_crop_matching_use_catalog_names(api):
    from app.api.routes_disease import _normalize_crop

    catalog = _catalog(api)
    farm = api.farmland(district="Gazipur")
    season = api.client.post("/advisor/seasons", json={
        "farmland_id": farm["id"], "crop_id": catalog["Maize"]["crop_id"],
    }).json()
    row = api.db.get(m2_advisor.Season, __import__("uuid").UUID(season["season_id"]))
    row.status = "active"
    api.db.commit()
    state = api.client.get(f"/farmlands/{farm['id']}/state").json()
    assert state["active_season"]["crop_name"] == "Maize"
    assert _normalize_crop("Maize") == _normalize_crop("Corn")
    for name in ("Potato", "Wheat", "Rice"):
        assert _normalize_crop(name) == _normalize_crop(name.upper())


def test_import_command_reports_conflicts_with_exit_status_3(db, monkeypatch, capsys):
    import app.core.database as database
    from scripts import import_reference_data

    db.add(Crop(id=uuid4(), name="Maize"))
    db.add(Crop(id=uuid4(), name="Corn"))
    db.commit()
    bind = db.get_bind()
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(autoflush=False, bind=bind))

    assert import_reference_data.run_import(EVALUATED_ON) == 3
    output = capsys.readouterr().out
    assert "CONFLICT: crop maize: several existing rows" in output
    assert import_reference_data.run_import(EVALUATED_ON) == 3  # still reported, nothing overwritten


def test_regional_entries_name_the_barc_crop_situation(api):
    farm = api.farmland(district="Cumilla", upazila="Adarsha Sadar", soil_type="Loam", land_type="high")
    body = recommend(api, farm["id"])
    rice = next(item for item in body["regional_context"] if item["crop"]["name"] == "Rice")
    assert {"Boro dhan", "T. Aman dhan"} <= {entry["source_crop_name"] for entry in rice["entries"]}
