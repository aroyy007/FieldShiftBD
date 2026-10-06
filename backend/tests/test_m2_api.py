"""HTTP and persistence integration checks for Module 2 API boundaries."""

import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.update(
    {
        "DB_USER": "fieldshift_test",
        "DB_PASSWORD": "fieldshift_test",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "fieldshift_test",
        "DATABASE_URL": "sqlite://",
    }
)

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.main import app
from app.models import AgriculturalKnowledge, Base, Crop, Farmer, Farmland, Task
from app.schemas.m2_advisor import FarmProfileInput


SCENARIO_PATH = Path(__file__).parent / "fixtures" / "m2" / "synthetic_golden_farm.json"
SCENARIO = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))


def synthetic_knowledge_rows(scenario, reviewer_id):
    """Build explicitly synthetic rows for an isolated integration-test DB."""
    crop_id = UUID(scenario["crop"]["crop_id"])
    rows = []
    for record in scenario["knowledge_records"]:
        rows.append(
            AgriculturalKnowledge(
                crop_id=crop_id,
                category=record["category"],
                content=record["content"],
                source_name="SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE",
                source_reference=f"fixture://{scenario['scenario_id']}/{record['category']}",
                review_status=record.get("review_status", "approved"),
                reviewed_by=reviewer_id,
                reviewed_at=datetime.now(timezone.utc),
                effective_from=date(2020, 1, 1),
                effective_to=date(2099, 12, 31),
            )
        )
    return rows


@pytest.fixture
def m2_client():
    profile = SCENARIO["farm_profile"]
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    saved_defaults = []
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is None:
                continue
            default_sql = str(column.server_default.arg)
            if "gen_random_uuid" in default_sql or "::jsonb" in default_sql:
                saved_defaults.append((column, column.server_default))
                column.server_default = None
    Base.metadata.create_all(engine)
    test_session = sessionmaker(autoflush=False, bind=engine)
    db = test_session()

    farmer = Farmer(
        id=UUID(profile["farmer_id"]),
        name="TEST ONLY Synthetic Farmer",
        phone_e164="+8801700000099",
    )
    other_farmer = Farmer(
        name="TEST ONLY Other Farmer",
        phone_e164="+8801700000098",
    )
    crop = Crop(
        id=UUID(SCENARIO["crop"]["crop_id"]),
        name=SCENARIO["crop"]["name"],
        scientific_name=SCENARIO["crop"]["scientific_name"],
    )
    db.add_all([farmer, other_farmer, crop])
    db.flush()
    farmland = Farmland(
        id=UUID(profile["farmland_id"]),
        farmer_id=farmer.id,
        name="TEST ONLY Synthetic Field",
        land_area_sqm=Decimal("8093.713"),
        land_area_display_unit="acre",
        country_code="BD",
        division=profile["location"]["division"],
        district=profile["location"]["district"],
        upazila=profile["location"]["upazila"],
        village_or_locality=profile["location"]["village_or_locality"],
        soil_type=profile["soil_type"],
        irrigation_available=profile["irrigation_available"],
        water_source=profile["water_source"],
        farming_method=profile["farming_method"],
    )
    other_farmland = Farmland(
        farmer_id=other_farmer.id,
        name="TEST ONLY Other Field",
        land_area_sqm=Decimal("1000"),
        land_area_display_unit="square_metre",
    )
    db.add_all([farmland, other_farmland])
    db.commit()

    def override_get_db():
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_farmer_id] = lambda: farmer.id
    try:
        with TestClient(app) as client:
            client.app.state.other_farmland_id = other_farmland.id
            client.app.state.other_farmer_id = other_farmer.id
            yield client, SCENARIO, db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        db.close()
        Base.metadata.drop_all(engine)
        for column, server_default in saved_defaults:
            column.server_default = server_default
        engine.dispose()


def test_m2_api_recommendation_selection_lifecycle_and_history(m2_client):
    client, scenario, db = m2_client
    profile = scenario["farm_profile"]
    farmland_id = profile["farmland_id"]
    db.add(synthetic_knowledge_rows(scenario, UUID(profile["farmer_id"]))[-1])
    db.commit()

    recommendation = client.post(
        "/advisor/recommendations",
        json=profile,
    )

    assert recommendation.status_code == 200
    assert recommendation.json()["status"] == "no_approved_knowledge"
    assert recommendation.json()["recommendations"] == []

    selection = client.post(
        "/advisor/seasons",
        json={
            "farmer_id": profile["farmer_id"],
            "farmland_id": farmland_id,
            "crop_id": scenario["crop"]["crop_id"],
            "planting_date": "2026-11-01",
            "expected_harvest_date": "2027-02-01",
        },
    )

    assert selection.status_code == 201
    assert selection.json()["status"] == "planned"
    assert selection.json()["budget_amount"] is None
    season_id = selection.json()["season_id"]

    activation = client.post(f"/advisor/seasons/{season_id}/activate")
    assert activation.status_code == 409
    assert activation.json()["detail"] == "Generate a season plan before activation"

    missing_evidence_plan = client.post(
        f"/advisor/seasons/{season_id}/plan",
        json={"season_id": season_id, "title": "Synthetic test plan"},
    )
    assert missing_evidence_plan.status_code == 409
    assert "No approved season-plan knowledge" in missing_evidence_plan.json()["detail"]

    history = client.get(f"/advisor/farmlands/{farmland_id}/seasons")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["season_id"] == season_id
    assert history.json()[0]["status"] == "planned"
    assert "current_growth_stage_id" not in history.json()[0]

    closing = client.post(
        f"/advisor/seasons/{season_id}/close",
        json={"season_id": season_id, "actual_yield": 5, "yield_unit": "kg"},
    )
    assert closing.status_code == 409


def test_m2_synthetic_scenario_matches_contract_and_completes_positive_api_flow(m2_client):
    client, scenario, db = m2_client
    profile = FarmProfileInput.model_validate(scenario["farm_profile"])
    assert profile.farmland_id == UUID(scenario["farm_profile"]["farmland_id"])
    assert "TEST ONLY" in scenario["test_only_warning"]
    assert "NOT AGRICULTURAL ADVICE" in scenario["test_only_warning"]

    db.add_all(synthetic_knowledge_rows(scenario, profile.farmer_id))
    db.commit()

    recommendation = client.post(
        "/advisor/recommendations",
        json=profile.model_dump(mode="json", by_alias=True),
    )
    assert recommendation.status_code == 200
    recommendation_body = recommendation.json()
    assert recommendation_body["status"] == "available"
    assert len(recommendation_body["recommendations"]) == 1
    crop_recommendation = recommendation_body["recommendations"][0]
    assert crop_recommendation["reasoning"]["positive_factors"][0]["factor"] == "soil"
    assert crop_recommendation["reasoning"]["risks_or_concerns"][0]["factor"] == "water"
    assert crop_recommendation["score"] is None
    assert crop_recommendation["knowledge_refs"][0]["source_name"] == (
        "SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE"
    )

    another_recommendation = client.post(
        "/advisor/recommendations",
        json=profile.model_dump(mode="json", by_alias=True),
    )
    assert another_recommendation.status_code == 200
    dismissible_id = another_recommendation.json()["recommendations"][0]["recommendation_id"]

    selection = client.post(
        "/advisor/seasons",
        json={
            "farmer_id": scenario["farm_profile"]["farmer_id"],
            "farmland_id": scenario["farm_profile"]["farmland_id"],
            "crop_id": scenario["crop"]["crop_id"],
            "recommendation_id": crop_recommendation["recommendation_id"],
            "planting_date": "2026-11-01",
            "expected_harvest_date": "2027-02-01",
            "budget_amount": 5000,
            "budget_currency": "BDT",
        },
    )
    assert selection.status_code == 201
    assert selection.json()["status"] == "planned"
    assert selection.json()["budget_amount"] == 5000.0
    assert isinstance(selection.json()["budget_amount"], (int, float))
    season_id = selection.json()["season_id"]

    saved_recommendations = client.get(
        f"/advisor/farmlands/{scenario['farm_profile']['farmland_id']}/recommendations"
    )
    assert saved_recommendations.status_code == 200
    statuses_by_id = {
        item["recommendation_id"]: item["status"] for item in saved_recommendations.json()
    }
    assert statuses_by_id[crop_recommendation["recommendation_id"]] == "selected"

    dismissed = client.post(f"/advisor/recommendations/{dismissible_id}/dismiss")
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"

    plan_response = client.post(
        f"/advisor/seasons/{season_id}/plan",
        json={"season_id": season_id, "title": "TEST ONLY synthetic plan", "status": "draft"},
    )
    assert plan_response.status_code == 201
    plan_body = plan_response.json()
    assert [stage["sequence"] for stage in plan_body["growth_stages"]] == [1, 2]
    assert (
        plan_body["initial_tasks"][0]["growth_stage_id"]
        == plan_body["growth_stages"][0]["growth_stage_id"]
    )
    assert plan_body["initial_tasks"][0]["due_day_offset"] == 4
    assert "status" not in plan_body["initial_tasks"][0]
    assert plan_body["knowledge_refs"][0]["source_name"] == (
        "SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE"
    )
    assert db.query(Task).count() == 0

    read_plan = client.get(f"/advisor/seasons/{season_id}/plan")
    assert read_plan.status_code == 200
    assert read_plan.json()["initial_tasks"] == plan_body["initial_tasks"]

    harvest = client.get(f"/advisor/seasons/{season_id}/harvest-guidance")
    assert harvest.status_code == 200
    assert (
        harvest.json()["guidance"]
        == scenario["knowledge_records"][2]["content"]["guidance"]
    )
    assert harvest.json()["knowledge_refs"][0]["source_type"] == "synthetic_test_fixture"

    activated = client.post(f"/advisor/seasons/{season_id}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    assert "current_growth_stage_id" not in activated.json()

    task_payload = {
        "tasks": [
            {
                "reference": f"{plan_body['season_plan_id']}-1",
                "growth_stage_id": plan_body["initial_tasks"][0]["growth_stage_id"],
                "title": plan_body["initial_tasks"][0]["title"],
                "description": plan_body["initial_tasks"][0]["description"],
                "days_after_planting": plan_body["initial_tasks"][0]["due_day_offset"],
                "priority": plan_body["initial_tasks"][0]["priority"],
            }
        ]
    }
    task_url = (
        f"/farmlands/{scenario['farm_profile']['farmland_id']}"
        f"/seasons/{season_id}/tasks/from-plan"
    )
    imported_tasks = client.post(task_url, json=task_payload)
    assert imported_tasks.status_code == 200
    assert imported_tasks.json()["created_count"] == 1
    assert imported_tasks.json()["existing_count"] == 0
    retried_import = client.post(task_url, json=task_payload)
    assert retried_import.status_code == 200
    assert retried_import.json()["created_count"] == 0
    assert retried_import.json()["existing_count"] == 1
    assert db.query(Task).count() == 1

    closed = client.post(
        f"/advisor/seasons/{season_id}/close",
        json={
            "season_id": season_id,
            "actual_harvest_date": "2027-02-05",
            "actual_yield": 8.5,
            "yield_unit": "kg",
            "outcome_notes": "TEST ONLY synthetic outcome",
        },
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "completed"
    assert closed.json()["actual_yield"] == 8.5
    assert isinstance(closed.json()["actual_yield"], (int, float))
    assert db.query(Task).count() == 1

    completed_plan = client.get(f"/advisor/seasons/{season_id}/plan")
    assert completed_plan.status_code == 200
    assert completed_plan.json()["status"] == "completed"

    history = client.get(
        f"/advisor/farmlands/{scenario['farm_profile']['farmland_id']}/seasons"
    )
    assert history.status_code == 200
    assert history.json()[0]["status"] == "completed"
    assert history.json()[0]["actual_yield"] == 8.5
    assert "current_growth_stage_id" not in history.json()[0]


def test_m2_api_requires_verified_farmer_identity(m2_client):
    client, scenario, _ = m2_client
    identity_override = app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.get(
            f"/advisor/farmlands/{scenario['farm_profile']['farmland_id']}/seasons"
        )
    finally:
        app.dependency_overrides[get_current_farmer_id] = identity_override

    assert response.status_code == 401


def test_m2_api_does_not_expose_another_farmers_data(m2_client):
    client, _, _ = m2_client
    other_farmland_id = client.app.state.other_farmland_id

    response = client.get(f"/advisor/farmlands/{other_farmland_id}/seasons")

    assert response.status_code == 404

    recommendation_response = client.post(
        "/advisor/recommendations",
        json={"farmland_id": str(other_farmland_id)},
    )
    assert recommendation_response.status_code == 404


def test_m2_resource_routes_hide_owned_records_from_other_farmers(m2_client):
    client, scenario, db = m2_client
    profile = scenario["farm_profile"]
    owner_id = UUID(profile["farmer_id"])
    db.add_all(synthetic_knowledge_rows(scenario, owner_id))
    db.commit()

    recommendations = client.post("/advisor/recommendations", json=profile)
    assert recommendations.status_code == 200
    recommendation_id = recommendations.json()["recommendations"][0]["recommendation_id"]
    season = client.post(
        "/advisor/seasons",
        json={
            "farmland_id": profile["farmland_id"],
            "crop_id": scenario["crop"]["crop_id"],
            "planting_date": "2026-11-01",
            "expected_harvest_date": "2027-02-01",
        },
    )
    assert season.status_code == 201
    season_id = season.json()["season_id"]
    plan = client.post(
        f"/advisor/seasons/{season_id}/plan",
        json={"season_id": season_id, "title": "TEST ONLY scoped plan"},
    )
    assert plan.status_code == 201

    identity_override = app.dependency_overrides[get_current_farmer_id]
    app.dependency_overrides[get_current_farmer_id] = lambda: client.app.state.other_farmer_id
    try:
        responses = [
            client.get(f"/advisor/farmlands/{profile['farmland_id']}/recommendations"),
            client.post(f"/advisor/recommendations/{recommendation_id}/dismiss"),
            client.post(
                "/advisor/seasons",
                json={
                    "farmer_id": profile["farmer_id"],
                    "farmland_id": profile["farmland_id"],
                    "crop_id": scenario["crop"]["crop_id"],
                },
            ),
            client.get(f"/advisor/farmlands/{profile['farmland_id']}/seasons"),
            client.post(f"/advisor/seasons/{season_id}/activate"),
            client.post(
                f"/advisor/seasons/{season_id}/plan",
                json={"season_id": season_id, "title": "TEST ONLY foreign plan"},
            ),
            client.get(f"/advisor/seasons/{season_id}/plan"),
            client.get(f"/advisor/seasons/{season_id}/harvest-guidance"),
            client.post(
                f"/advisor/seasons/{season_id}/close",
                json={"season_id": season_id, "actual_yield": 3},
            ),
        ]
    finally:
        app.dependency_overrides[get_current_farmer_id] = identity_override

    assert [response.status_code for response in responses] == [404] * len(responses)


def test_api_refuses_to_infer_suitability_from_risk_only_knowledge(m2_client):
    client, scenario, db = m2_client
    risk_only = dict(scenario["knowledge_records"][0])
    risk_only["content"] = dict(risk_only["content"])
    risk_only["content"].pop("suitable_because")
    synthetic_scenario = {**scenario, "knowledge_records": [risk_only]}
    reviewer_id = UUID(scenario["farm_profile"]["farmer_id"])
    db.add(synthetic_knowledge_rows(synthetic_scenario, reviewer_id)[0])
    db.commit()

    response = client.post("/advisor/recommendations", json=scenario["farm_profile"])

    assert response.status_code == 200
    assert response.json()["status"] == "no_supported_fit"
    assert response.json()["recommendations"] == []


def test_m2_api_validation_and_missing_resources_return_contract_errors(m2_client):
    client, scenario, _ = m2_client
    profile = scenario["farm_profile"]
    missing_id = "99999999-9999-4999-8999-999999999999"

    missing_profile = client.post(
        "/advisor/recommendations", json={"soil_type": "Synthetic loam"}
    )
    assert missing_profile.status_code == 422

    invalid_dates = client.post(
        "/advisor/seasons",
        json={
            "farmland_id": profile["farmland_id"],
            "crop_id": scenario["crop"]["crop_id"],
            "planting_date": "2027-02-01",
            "expected_harvest_date": "2026-11-01",
        },
    )
    assert invalid_dates.status_code == 422

    missing_history = client.get(f"/advisor/farmlands/{missing_id}/seasons")
    assert missing_history.status_code == 404

    mismatched_close = client.post(
        f"/advisor/seasons/{missing_id}/close",
        json={"season_id": profile["farmland_id"]},
    )
    assert mismatched_close.status_code == 422
