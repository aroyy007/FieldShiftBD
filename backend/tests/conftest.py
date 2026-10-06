"""Shared SQLite test setup for the PostgreSQL-backed API models."""

import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# App settings are instantiated during module import; set the fake database
# environment before importing any application module.
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


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_, compiler, **kwargs):
    """Use SQLite's JSON storage when compiling PostgreSQL JSONB in tests."""
    return "JSON"


from app.core.auth import get_current_farmer_id
from app.core.database import get_db
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
