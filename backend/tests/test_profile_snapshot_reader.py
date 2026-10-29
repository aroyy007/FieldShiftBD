from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.models import (
    Crop,
    Farmland,
    Farmer,
    FarmlandCropPreference,
    GrowthStage,
    Season,
    SeasonPlan,
)
from app.services.profile_intake.snapshot import (
    DatabaseFarmProfileSnapshotReader,
    FarmSnapshotNotFound,
)

NOW = datetime(2026, 10, 29, 9, tzinfo=timezone.utc)


def test_reader_maps_existing_m1_m2_m3_fields_without_inventing_missing_data(foundation_sessions):
    with foundation_sessions() as db:
        farmer = Farmer(name="SYNTHETIC TEST ONLY", phone_e164="+8801700000321")
        aman = Crop(name="SYNTHETIC TEST ONLY Aman")
        lentil = Crop(name="SYNTHETIC TEST ONLY Lentil")
        db.add_all([farmer, aman, lentil])
        db.flush()
        farm = Farmland(
            farmer_id=farmer.id,
            name="SYNTHETIC TEST ONLY field",
            division="SYNTHETIC DIVISION",
            district="SYNTHETIC DISTRICT",
            upazila="SYNTHETIC UPAZILA",
            village_or_locality="SYNTHETIC LOCALITY",
            latitude=Decimal("24.000000"),
            longitude=Decimal("89.000000"),
            land_area_sqm=Decimal("4000"),
            land_area_display_unit="decimal",
            soil_type="SYNTHETIC LOAM",
            land_type="medium_high",
            irrigation_available=False,
            water_source=None,
            equipment=["synthetic_pump"],
            budget_amount=Decimal("15000.00"),
            budget_currency="BDT",
        )
        db.add(farm)
        db.flush()
        db.add(FarmlandCropPreference(
            farmland_id=farm.id,
            crop_id=lentil.id,
            preference_rank=1,
            notes="SYNTHETIC TEST ONLY priority",
        ))
        old_season = Season(
            farmland_id=farm.id,
            crop_id=lentil.id,
            status="completed",
            planting_date=date(2025, 11, 1),
            actual_harvest_date=date(2026, 2, 1),
            actual_yield=Decimal("120.0"),
            yield_unit="kg",
        )
        active_season = Season(
            farmland_id=farm.id,
            crop_id=aman.id,
            status="active",
            planting_date=date(2026, 7, 1),
            expected_harvest_date=date(2026, 11, 1),
        )
        db.add_all([old_season, active_season])
        db.flush()
        plan = SeasonPlan(season_id=active_season.id, title="SYNTHETIC TEST ONLY plan", status="active")
        db.add(plan)
        db.flush()
        stage = GrowthStage(season_plan_id=plan.id, name="SYNTHETIC TEST ONLY stage", sequence=1)
        db.add(stage)
        db.flush()
        active_season.current_growth_stage_id = stage.id
        farm_id = farm.id
        db.commit()

        snapshot = DatabaseFarmProfileSnapshotReader(
            db,
            clock=lambda: NOW,
            district_code_resolver=lambda _district: "SYN-81",
        ).get_snapshot(farmer.id, farm.id)
        other_farmer_id = Farmer(name="SYNTHETIC TEST ONLY other", phone_e164="+8801700000322")
        db.add(other_farmer_id)
        db.commit()
        other_id = other_farmer_id.id

        assert snapshot.profile.district_code == "SYN-81"
        assert snapshot.profile.village_or_locality == "SYNTHETIC LOCALITY"
        assert snapshot.profile.irrigation_available is False
        assert snapshot.profile.water_source is None
        assert snapshot.profile.budget_amount == 15000
        assert snapshot.active_season.crop_code == aman.name
        assert snapshot.active_season.current_growth_stage_name == stage.name
        assert snapshot.crop_priorities[0].crop_code == lentil.name
        assert snapshot.rotation_history[0].crop_code == lentil.name
        assert snapshot.provenance[0].quality_status == "provisional"

    with foundation_sessions() as db:
        with pytest.raises(FarmSnapshotNotFound):
            DatabaseFarmProfileSnapshotReader(db, clock=lambda: NOW).get_snapshot(other_id, farm_id)


def test_reader_returns_no_active_season_instead_of_placeholder_crop(foundation_sessions):
    with foundation_sessions() as db:
        farmer = Farmer(name="SYNTHETIC TEST ONLY", phone_e164="+8801700000323")
        crop = Crop(name="SYNTHETIC TEST ONLY Crop")
        db.add_all([farmer, crop])
        db.flush()
        farm = Farmland(
            farmer_id=farmer.id,
            name="SYNTHETIC TEST ONLY field",
            land_area_sqm=1000,
            land_area_display_unit="square_metre",
        )
        db.add(farm)
        db.commit()

        snapshot = DatabaseFarmProfileSnapshotReader(db, clock=lambda: NOW).get_snapshot(farmer.id, farm.id)

    assert snapshot.active_season is None
    assert snapshot.crop_priorities == []
    assert snapshot.rotation_history == []
