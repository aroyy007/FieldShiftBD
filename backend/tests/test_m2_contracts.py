"""Contract-focused tests for the M1 → M2 and M2 → M3 payloads."""

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.m2_advisor import (
    CropSelectionRequest,
    FarmProfileInput,
    GrowthStageDefinition,
    InitialTaskDefinition,
    SeasonPlanResponse,
)


def test_m1_farm_profile_accepts_agreed_profile_concepts() -> None:
    profile = FarmProfileInput.model_validate({
        "farmer_id": "11111111-1111-4111-8111-111111111111",
        "farmland_id": "22222222-2222-4222-8222-222222222222",
        "location": {"country_code": "BD", "district": "Comilla"},
        "land_area": "2",
        "land_unit": "acre",
        "soil_type": "loamy",
        "irrigation_available": True,
        "water_source": "canal",
        "previous_crop": {"crop_name": "synthetic test crop", "yield_amount": "12", "yield_unit": "kg"},
        "previous_yield": "12",
        "equipment": ["pump"],
        "farming_experience": "4",
        "farming_method": "conventional",
        "budget": "2000",
        "budget_currency": "BDT",
        "crop_preferences": [],
        "livestock": [],
    })

    assert profile.farmland_id == UUID("22222222-2222-4222-8222-222222222222")
    assert profile.location.district == "Comilla"
    assert profile.land_area == Decimal("2")
    assert profile.previous_crop.yield_amount == Decimal("12")
    assert profile.previous_yield == Decimal("12")
    assert profile.farming_experience_years == Decimal("4")
    assert profile.budget_amount == Decimal("2000")
    assert profile.model_dump(by_alias=True)["farming_experience"] == Decimal("4")
    assert profile.model_dump(by_alias=True)["budget"] == Decimal("2000")
    contract_fields = set(FarmProfileInput.model_json_schema(mode="validation")["properties"])
    assert {
        "farmer_id", "location", "land_area", "land_unit", "soil_type",
        "irrigation_available", "water_source", "previous_crop", "previous_yield",
        "equipment", "farming_experience", "farming_method", "budget",
        "crop_preferences", "livestock",
    }.issubset(contract_fields)


def test_nested_previous_crop_yield_remains_compatible_and_conflicts_are_rejected() -> None:
    profile = FarmProfileInput.model_validate({
        "farmland_id": "22222222-2222-4222-8222-222222222222",
        "previous_crop": {"crop_name": "synthetic test crop", "yield_amount": "6"},
    })
    assert profile.previous_yield == Decimal("6")

    with pytest.raises(ValidationError):
        FarmProfileInput.model_validate({
            "farmland_id": "22222222-2222-4222-8222-222222222222",
            "previous_crop": {"yield_amount": "6"},
            "previous_yield": "7",
        })


def test_farm_profile_allows_missing_progressive_intake_fields() -> None:
    profile = FarmProfileInput(farmland_id=UUID("22222222-2222-4222-8222-222222222222"))
    assert profile.soil_type is None
    assert profile.irrigation_available is None
    assert profile.equipment == []


def test_m2_to_m3_season_plan_and_growth_stage_contract() -> None:
    plan = SeasonPlanResponse.model_validate({
        "season_id": "33333333-3333-4333-8333-333333333333",
        "season_plan_id": "44444444-4444-4444-8444-444444444444",
        "title": "Synthetic test plan",
        "status": "draft",
        "growth_stages": [{
            "growth_stage_id": "55555555-5555-4555-8555-555555555555",
            "name": "Synthetic stage one", "sequence": 1, "start_day": 0, "end_day": 10,
        }],
        "initial_tasks": [{
            "title": "Synthetic task definition", "growth_stage_sequence": 1,
            "due_day_offset": 2, "source": "season_plan",
        }],
    })

    assert plan.growth_stages[0].sequence == 1
    assert plan.initial_tasks[0].growth_stage_sequence == 1
    assert plan.initial_tasks[0].source == "season_plan"
    operational_fields = {
        "status", "completed", "pending", "skipped", "overdue", "completed_at",
        "completion_timestamp", "farm_state_status", "task_id",
    }
    assert not operational_fields.intersection(InitialTaskDefinition.model_fields)
    assert {"name", "sequence", "start_day", "end_day"}.issubset(GrowthStageDefinition.model_fields)
    assert {"season_id", "growth_stages", "initial_tasks"}.issubset(SeasonPlanResponse.model_fields)
    assert "current_growth_stage_id" not in SeasonPlanResponse.model_fields


def test_stage_dates_must_be_ordered() -> None:
    with pytest.raises(ValidationError):
        GrowthStageDefinition(name="bad synthetic stage", sequence=1, start_day=8, end_day=4)


def test_crop_selection_contract_rejects_invalid_date_order():
    with pytest.raises(ValidationError):
        CropSelectionRequest(
            farmland_id=UUID("22222222-2222-4222-8222-222222222222"),
            crop_id=UUID("33333333-3333-4333-8333-333333333333"),
            planting_date=date(2026, 12, 1), expected_harvest_date=date(2026, 11, 1),
        )


def test_initial_task_is_only_a_definition_for_m3() -> None:
    task = InitialTaskDefinition(title="Synthetic task", due_day_offset=3)
    assert task.model_dump(exclude_none=True) == {
        "title": "Synthetic task", "due_day_offset": 3, "priority": "normal", "source": "season_plan"
    }
    assert "status" not in task.model_dump()
