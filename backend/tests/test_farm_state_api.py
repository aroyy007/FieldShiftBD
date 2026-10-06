import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import text
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

from app.core.database import get_db
from app.core.auth import get_current_farmer_id
from app.main import app
from app.models import (
    Base,
    Crop,
    CropVariety,
    Farmer,
    Farmland,
    GrowthStage,
    Season,
    SeasonPlan,
)


@pytest.fixture
def client_and_farm():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is None:
                continue
            default_sql = str(column.server_default.arg)
            if "gen_random_uuid" in default_sql or "::jsonb" in default_sql:
                column.server_default = None
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(autoflush=False, bind=engine)
    db = TestSession()

    farmer = Farmer(name="Test Farmer", phone_e164="+8801700000000")
    other_farmer = Farmer(name="Other Farmer", phone_e164="+8801700000001")
    crop = Crop(name="Rice")
    db.add_all([farmer, other_farmer, crop])
    db.flush()

    farmland = Farmland(
        farmer_id=farmer.id,
        name="Test Field",
        land_area_sqm=Decimal("1000"),
        land_area_display_unit="square_metre",
    )
    other_farmland = Farmland(
        farmer_id=other_farmer.id,
        name="Other Field",
        land_area_sqm=Decimal("2000"),
        land_area_display_unit="square_metre",
    )
    variety = CropVariety(crop_id=crop.id, name="BRRI dhan 28")
    db.add_all([farmland, other_farmland, variety])
    db.flush()

    season = Season(
        farmland_id=farmland.id,
        crop_id=crop.id,
        crop_variety_id=variety.id,
        variety_name=variety.name,
        planting_date=date(2026, 9, 1),
        expected_harvest_date=date(2026, 12, 1),
        status="active",
    )
    db.add(season)
    db.flush()

    plan = SeasonPlan(season_id=season.id, title="Rice season", status="active")
    db.add(plan)
    db.flush()

    stage = GrowthStage(
        season_plan_id=plan.id,
        name="Vegetative",
        sequence=1,
        start_day=10,
        end_day=40,
    )
    db.add(stage)
    db.flush()
    season.current_growth_stage_id = stage.id
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_farmer_id] = lambda: farmer.id
    with TestClient(app) as test_client:
        test_client.app.state.other_farmland_id = other_farmland.id
        yield test_client, farmland.id, season.id, stage.id

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_farm_state_requires_authenticated_farmer(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    authentication = app.dependency_overrides.pop(get_current_farmer_id)

    response = client.get(f"/farmlands/{farmland_id}/state")

    app.dependency_overrides[get_current_farmer_id] = authentication
    assert response.status_code == 401


def test_farmland_reads_are_scoped_to_authenticated_farmer(client_and_farm):
    client, _, _, _ = client_and_farm
    other_farmland_id = client.app.state.other_farmland_id

    response = client.get(f"/farmlands/{other_farmland_id}/state")

    assert response.status_code == 404


def test_plan_tasks_are_materialized_once_and_keep_season_plan_source(client_and_farm):
    client, farmland_id, season_id, stage_id = client_and_farm
    url = f"/farmlands/{farmland_id}/seasons/{season_id}/tasks/from-plan"
    payload = {
        "tasks": [
            {
                "reference": "top-dressing-1",
                "growth_stage_id": str(stage_id),
                "title": "Apply first top dressing",
                "days_after_planting": 18,
                "priority": "high",
            }
        ]
    }

    first = client.post(url, json=payload)
    second = client.post(url, json=payload)

    assert first.status_code == 200
    assert first.json()["created_count"] == 1
    assert first.json()["tasks"][0]["source"] == "season_plan"
    assert first.json()["tasks"][0]["source_reference"] == "season-plan:top-dressing-1"
    assert first.json()["tasks"][0]["due_at"].startswith("2026-09-19T17:59:59")
    assert second.status_code == 200
    assert second.json()["created_count"] == 0
    assert second.json()["existing_count"] == 1


def test_weather_task_and_problem_are_written_to_farm_state(client_and_farm):
    client, farmland_id, season_id, stage_id = client_and_farm
    task_response = client.post(
        f"/farmlands/{farmland_id}/tasks",
        json={
            "season_id": str(season_id),
            "growth_stage_id": str(stage_id),
            "title": "Check drainage before rain",
            "source": "weather",
            "source_reference": "weather-event:rain-2026-10-07",
            "priority": "urgent",
        },
    )
    problem_response = client.post(
        f"/farmlands/{farmland_id}/problems",
        json={
            "season_id": str(season_id),
            "source": "weather",
            "category": "waterlogging_risk",
            "description": "Heavy rain may flood the lower field.",
            "severity": "high",
        },
    )

    assert task_response.status_code == 201
    assert task_response.json()["source"] == "weather"
    assert problem_response.status_code == 201
    assert problem_response.json()["status"] == "open"

    state = client.get(f"/farmlands/{farmland_id}/state")
    assert state.status_code == 200
    assert state.json()["tasks"][0]["title"] == "Check drainage before rain"
    assert state.json()["open_problems"][0]["category"] == "waterlogging_risk"


def test_completing_task_records_timestamp_and_wins_over_overdue_state(client_and_farm):
    client, farmland_id, season_id, stage_id = client_and_farm
    created = client.post(
        f"/farmlands/{farmland_id}/tasks",
        json={
            "season_id": str(season_id),
            "growth_stage_id": str(stage_id),
            "title": "Inspect field",
            "due_at": "2026-09-02T00:00:00Z",
        },
    )
    task_id = created.json()["id"]

    response = client.patch(
        f"/farmlands/{farmland_id}/tasks/{task_id}",
        json={"status": "completed"},
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["schedule_state"] == "completed"
    assert response.json()["completed_at"] is not None


def test_checkin_is_persisted_and_included_in_farm_state(client_and_farm):
    client, farmland_id, season_id, stage_id = client_and_farm
    response = client.post(
        f"/farmlands/{farmland_id}/check-ins",
        json={
            "season_id": str(season_id),
            "growth_stage_id": str(stage_id),
            "notes": "Leaves look healthy after irrigation.",
            "observations": {"water_condition": "adequate"},
        },
    )

    assert response.status_code == 201
    assert response.json()["observations"]["water_condition"] == "adequate"
    state = client.get(f"/farmlands/{farmland_id}/state")
    assert state.json()["latest_checkin"]["id"] == response.json()["id"]


def test_growth_stage_update_rejects_stage_outside_seasons_plan(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    response = client.patch(
        f"/farmlands/{farmland_id}/state/growth-stage",
        json={"growth_stage_id": "00000000-0000-0000-0000-000000000999"},
    )

    assert response.status_code == 404


def test_growth_stage_update_changes_the_shared_farm_state(client_and_farm):
    client, farmland_id, _, stage_id = client_and_farm

    response = client.patch(
        f"/farmlands/{farmland_id}/state/growth-stage",
        json={"growth_stage_id": str(stage_id)},
    )
    state = client.get(f"/farmlands/{farmland_id}/state")

    assert response.status_code == 200
    assert response.json()["name"] == "Vegetative"
    assert state.json()["current_growth_stage"]["id"] == str(stage_id)


def test_problem_resolution_is_timestamped_and_can_be_reopened(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    created = client.post(
        f"/farmlands/{farmland_id}/problems",
        json={
            "season_id": str(season_id),
            "source": "disease_detection",
            "category": "leaf_disease",
            "description": "Possible fungal disease on lower leaves.",
            "severity": "moderate",
        },
    )
    problem_id = created.json()["id"]

    resolved = client.patch(
        f"/farmlands/{farmland_id}/problems/{problem_id}",
        json={"status": "resolved"},
    )
    reopened = client.patch(
        f"/farmlands/{farmland_id}/problems/{problem_id}",
        json={"status": "open"},
    )

    assert created.status_code == 201
    assert resolved.json()["resolved_at"] is not None
    assert reopened.json()["status"] == "open"
    assert reopened.json()["resolved_at"] is None


def test_weather_task_source_reference_is_idempotent(client_and_farm):
    client, farmland_id, season_id, stage_id = client_and_farm
    payload = {
        "season_id": str(season_id),
        "growth_stage_id": str(stage_id),
        "title": "Open drainage channels",
        "source": "weather",
        "source_reference": "weather-event:storm-1",
    }

    created = client.post(f"/farmlands/{farmland_id}/tasks", json=payload)
    duplicate = client.post(f"/farmlands/{farmland_id}/tasks", json=payload)

    assert created.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == created.json()["id"]
