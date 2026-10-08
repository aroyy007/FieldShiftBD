"""PostgreSQL integration: migrations + real ingestion + M1 → M2 HTTP flow.

Runs only when ``FIELDSHIFT_PG_TEST_DATABASE_URL`` points at an isolated,
migrated test database (never the development database), for example:

    FIELDSHIFT_PG_TEST_DATABASE_URL=postgresql+psycopg2://user:pass@db:5432/fieldshift_m2_test \
        python -m pytest tests/test_pg_reference_integration.py

Farmers created here are generated TEST ONLY fixtures with random phone numbers.
Authentication uses the real register endpoint and JWT middleware.
"""

import json
import os
import random
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

PG_URL = os.environ.get("FIELDSHIFT_PG_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="set FIELDSHIFT_PG_TEST_DATABASE_URL to an isolated test DB")

EVALUATED_ON = date(2026, 10, 8)
SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "app/data/m2_knowledge_sources/barc_potato_comilla_snapshot.json"


@pytest.fixture(scope="module")
def pg_session_factory():
    assert "fieldshift_db" not in PG_URL.rsplit("/", 1)[-1], "refusing to run against the development database"
    engine = create_engine(PG_URL)
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar()
    assert version == "a7c4e2d91b30", "migrate the test database with `alembic upgrade head` first"
    yield sessionmaker(autoflush=False, bind=engine)
    engine.dispose()


def _import(session_factory):
    from app.services.m1_catalog_import import import_crop_catalog
    from app.services.m2_source_import import import_barc_snapshot, import_portal_knowledge

    with session_factory() as db:
        catalog = import_crop_catalog(db)
        import_barc_snapshot(
            db, json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")),
            evaluated_on=EVALUATED_ON, crop_id=catalog.crop_ids["potato"],
        )
        knowledge = import_portal_knowledge(db, catalog.crop_ids, evaluated_on=EVALUATED_ON)
        db.commit()
        return catalog, knowledge


def test_postgres_ingestion_is_idempotent(pg_session_factory):
    from app.models import AgriculturalKnowledge, Crop

    first_catalog, _ = _import(pg_session_factory)
    second_catalog, second = _import(pg_session_factory)
    assert first_catalog.crop_ids == second_catalog.crop_ids
    assert second.created == 0 and second.refreshed == 0 and second.conflicts == []
    with pg_session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Crop)) >= 4
        approved = db.scalar(select(func.count()).select_from(AgriculturalKnowledge).where(
            AgriculturalKnowledge.review_status == "approved",
            AgriculturalKnowledge.reviewed_by.is_(None),
        ))
        assert approved >= 309  # 308 portal-policy rows + legacy BARC snapshot


@pytest.fixture
def client(pg_session_factory):
    from app.core.database import get_db
    from app.main import app
    from app.services import m2_advisor

    _import(pg_session_factory)

    def override_get_db():
        session = pg_session_factory()
        try:
            yield session
        finally:
            session.close()

    previous = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    with patch.object(m2_advisor, "_farm_today", return_value=date(2026, 10, 10)):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def _register(client):
    phone = f"+88017{random.randint(10_000_000, 99_999_999)}"
    response = client.post("/auth/register", json={"name": "TEST ONLY PG farmer", "phone_e164": phone})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_postgres_m1_to_m2_flow_with_real_auth(client):
    headers = _register(client)
    farm = client.post("/farmlands", headers=headers, json={
        "name": "TEST ONLY PG field", "land_area_sqm": 8093.71, "land_area_display_unit": "acre",
        "division": "Chattogram", "district": "Comilla", "upazila": "Adarsha Sadar",
        "soil_type": "দোআঁশ", "land_type": "high", "irrigation_available": True,
    })
    assert farm.status_code == 201, farm.text
    farm_id = farm.json()["id"]
    assert farm.json()["district"] == "Cumilla"

    body = client.post(f"/advisor/farmlands/{farm_id}/recommendations", headers=headers).json()
    assert body["status"] == "available"
    assert {item["crop"]["name"] for item in body["recommendations"]} == {"Potato", "Wheat"}
    assert body["regional_context"]

    crops = {crop["name"]: crop for crop in client.get("/crops").json()}
    variety = next(v for v in crops["Potato"]["varieties"] if v["name"] == "BARI Alu-7 (Diamant)")
    potato = next(item for item in body["recommendations"] if item["crop"]["name"] == "Potato")
    season = client.post("/advisor/seasons", headers=headers, json={
        "farmland_id": farm_id, "crop_id": potato["crop"]["crop_id"],
        "crop_variety_id": variety["crop_variety_id"], "recommendation_id": potato["recommendation_id"],
        "planting_date": "2026-11-20",
    })
    assert season.status_code == 201, season.text
    season_id = season.json()["season_id"]
    harvest = client.get(f"/advisor/seasons/{season_id}/harvest-guidance", headers=headers).json()
    assert harvest["recommended_window_start"] == "2027-02-18"
    plan = client.post(f"/advisor/seasons/{season_id}/plan", headers=headers,
                       json={"season_id": season_id, "title": "Plan"})
    assert plan.status_code == 409

    saved = client.get(f"/advisor/farmlands/{farm_id}/recommendations", headers=headers).json()
    assert {item["status"] for item in saved} >= {"selected"}

    other = _register(client)
    assert client.post(f"/advisor/farmlands/{farm_id}/recommendations", headers=other).status_code == 404
    assert client.get(f"/advisor/seasons/{season_id}/harvest-guidance", headers=other).status_code == 404
    assert client.post(f"/advisor/farmlands/{farm_id}/recommendations").status_code == 401

    incomplete = client.post("/farmlands", headers=headers, json={
        "name": "TEST ONLY incomplete", "land_area_sqm": 1000, "district": "Gazipur",
    }).json()
    result = client.post(f"/advisor/farmlands/{incomplete['id']}/recommendations", headers=headers).json()
    assert result["status"] == "profile_incomplete"
    assert set(result["missing_profile_fields"]) == {"land_type", "soil_type"}
