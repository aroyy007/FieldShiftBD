"""HTTP and persistence integration checks for Module 2 API boundaries."""

import os
from decimal import Decimal

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

from app.core.database import get_db
from app.main import app
from app.models import Base, Crop, Farmer, Farmland


@pytest.fixture
def m2_client():
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

    farmer = Farmer(name="M2 API Test Farmer", phone_e164="+8801700000099")
    crop = Crop(name="Synthetic API Test Crop")
    db.add_all([farmer, crop])
    db.flush()
    farmland = Farmland(
        farmer_id=farmer.id,
        name="Synthetic API Test Field",
        land_area_sqm=Decimal("1000"),
        land_area_display_unit="square_metre",
    )
    db.add(farmland)
    db.commit()

    def override_get_db():
        yield db

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, farmer.id, farmland.id, crop.id
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        db.close()
        Base.metadata.drop_all(engine)
        for column, server_default in saved_defaults:
            column.server_default = server_default
        engine.dispose()


def test_m2_api_recommendation_selection_lifecycle_and_history(m2_client):
    client, farmer_id, farmland_id, crop_id = m2_client

    recommendation = client.post(
        "/advisor/recommendations",
        json={
            "farmer_id": str(farmer_id),
            "farmland_id": str(farmland_id),
            "soil_type": "synthetic test soil",
        },
    )

    assert recommendation.status_code == 200
    assert recommendation.json()["status"] == "no_approved_knowledge"
    assert recommendation.json()["recommendations"] == []

    selection = client.post(
        "/advisor/seasons",
        json={
            "farmer_id": str(farmer_id),
            "farmland_id": str(farmland_id),
            "crop_id": str(crop_id),
            "planting_date": "2026-11-01",
            "expected_harvest_date": "2027-02-01",
        },
    )

    assert selection.status_code == 201
    assert selection.json()["status"] == "planned"
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
