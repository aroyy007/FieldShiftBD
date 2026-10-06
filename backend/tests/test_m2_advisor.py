"""M2 service behavior with explicitly synthetic test knowledge and mock storage."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
pytest.importorskip("sqlalchemy", reason="M2 service tests require backend dependencies from backend/requirements.txt")
from sqlalchemy.dialects import postgresql

from app.models.core import Crop, Farmland
from app.models.season import CropRecommendation as RecommendationRecord, GrowthStage, Season, SeasonPlan
from app.models.state import Task
from app.schemas.m2_advisor import (
    FarmProfileInput,
    SeasonOutcomeInput,
    SeasonPlanCreate,
    SeasonPlanStatus,
)
from app.services import m2_advisor as service


FARM_ID = UUID("22222222-2222-4222-8222-222222222222")
FARMER_ID = UUID("11111111-1111-4111-8111-111111111111")
CROP_ID = UUID("33333333-3333-4333-8333-333333333333")
SEASON_ID = UUID("44444444-4444-4444-8444-444444444444")


class MemorySession:
    """Small M2 test double; no production or agronomic data is seeded."""

    def __init__(self, objects=None, scalar_results=None, scalars_result=None):
        self.objects = objects or {}
        self.scalar_results = list(scalar_results or [])
        self.scalars_result = list(scalars_result or [])
        self.added = []
        self.commits = 0

    def get(self, model, identifier):
        return self.objects.get((model, identifier))

    def scalars(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        if entity in {Crop, GrowthStage}:
            return iter(self.scalars_result)
        if entity is Season:
            return iter(self.scalars_result)
        return iter([])

    def scalar(self, statement):
        return self.scalar_results.pop(0) if self.scalar_results else None

    def execute(self, statement):
        return SimpleNamespace(all=lambda: [])

    def add(self, value):
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid4()

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        if not getattr(value, "created_at", None):
            value.created_at = datetime.now(timezone.utc)
        if hasattr(value, "updated_at") and not value.updated_at:
            value.updated_at = datetime.now(timezone.utc)


def synthetic_knowledge(*, content=None, category="crop_suitability", review_status="approved", crop_variety_id=None):
    """Synthetic-only record; never suitable for production seed data."""
    return SimpleNamespace(
        id=uuid4(), crop_id=CROP_ID, crop_variety_id=crop_variety_id,
        category=category, region_code=None,
        content=content or {
            "applicability": {"soil_type": "synthetic loam"},
            "suitable_because": [{"factor": "soil", "explanation": "Synthetic test evidence only."}],
            "concerns": [{"factor": "water", "explanation": "Synthetic test concern only."}],
        },
        source_name="SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE",
        source_type="synthetic_test_fixture",
        source_reference="unit-test-only", effective_from=date(2020, 1, 1),
        effective_to=date(2099, 12, 31), review_status=review_status,
        reviewed_by=None, reviewed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


def test_recommendations_include_factor_explanations_and_provenance():
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID)
    crop = SimpleNamespace(id=CROP_ID, name="Synthetic crop", scientific_name=None)
    db = MemorySession(objects={(Farmland, FARM_ID): farmland}, scalars_result=[crop])
    profile = FarmProfileInput(farmland_id=FARM_ID, soil_type="synthetic loam")

    with patch.object(service, "_approved_knowledge", return_value=[synthetic_knowledge()]):
        result = service.recommend_crops(db, profile)

    assert result.status == "available"
    assert result.recommendations[0].reasoning.positive_factors[0].factor == "soil"
    assert result.recommendations[0].reasoning.risks_or_concerns[0].knowledge_refs[0].source_reference == "unit-test-only"
    assert result.recommendations[0].score is None
    assert len([row for row in db.added if isinstance(row, RecommendationRecord)]) == 1


def test_recommendation_reports_missing_approved_knowledge_explicitly():
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID)
    crop = SimpleNamespace(id=CROP_ID, name="Synthetic crop", scientific_name=None)
    db = MemorySession(objects={(Farmland, FARM_ID): farmland}, scalars_result=[crop])

    with patch.object(service, "_approved_knowledge", return_value=[]):
        result = service.recommend_crops(db, FarmProfileInput(farmland_id=FARM_ID))

    assert result.status == "no_approved_knowledge"
    assert result.recommendations == []
    assert "cannot be established" in result.message


def test_positive_evidence_must_match_profile_and_limiting_factors_are_preserved():
    knowledge = synthetic_knowledge(content={
        "applicability": {"soil_type": "different synthetic soil"},
        "suitable_because": [{"factor": "soil", "explanation": "Synthetic positive."}],
        "limiting_factors": [{"factor": "budget", "explanation": "Synthetic limit."}],
    })
    profile = FarmProfileInput(farmland_id=FARM_ID, soil_type="synthetic loam")
    reasoning, _ = service._recommendation_reasoning(profile, [knowledge])
    assert reasoning.positive_factors == []
    assert reasoning.limiting_factors[0].factor == "budget"


def test_no_supported_crop_is_reported_when_positive_conditions_do_not_match():
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID)
    crop = SimpleNamespace(id=CROP_ID, name="Synthetic crop", scientific_name=None)
    db = MemorySession(objects={(Farmland, FARM_ID): farmland}, scalars_result=[crop])
    mismatched = synthetic_knowledge(content={
        "applicability": {"soil_type": "different synthetic soil"},
        "suitable_because": [{"factor": "soil", "explanation": "Synthetic test positive."}],
    })
    with patch.object(service, "_approved_knowledge", return_value=[mismatched]):
        result = service.recommend_crops(
            db, FarmProfileInput(farmland_id=FARM_ID, soil_type="synthetic loam")
        )
    assert result.status == "no_supported_fit"
    assert result.recommendations == []


def test_knowledge_query_requires_approved_and_effective_records():
    class CapturingSession:
        statement = None

        def scalars(self, statement):
            self.statement = statement
            return []

    db = CapturingSession()
    service._approved_knowledge(db, CROP_ID, date(2026, 10, 6), region_values={"BD"})
    compiled = db.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "review_status" in sql
    assert "approved" in compiled.params.values()
    assert "effective_from" in sql and "effective_to" in sql


def test_crop_selection_creates_planned_season_and_validates_crop():
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID)
    crop = SimpleNamespace(id=CROP_ID)
    db = MemorySession(objects={(Farmland, FARM_ID): farmland, (Crop, CROP_ID): crop})
    response = service.select_crop(db, FARM_ID, FARMER_ID, CROP_ID, None, None, None,
                                   date(2026, 11, 1), date(2027, 2, 1), Decimal("100"), "BDT")
    assert response.status == "planned"
    assert response.planting_date == date(2026, 11, 1)
    assert any(isinstance(row, Season) for row in db.added)

    with pytest.raises(service.M2NotFoundError):
        service.select_crop(db, FARM_ID, FARMER_ID, uuid4(), None, None, None,
                            None, None, None, "BDT")


def test_valid_non_recommended_crop_can_be_planned_alongside_current_active_season():
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID)
    crop = SimpleNamespace(id=CROP_ID)
    active = SimpleNamespace(id=uuid4(), farmland_id=FARM_ID, status="active")
    db = MemorySession(objects={(Farmland, FARM_ID): farmland, (Crop, CROP_ID): crop})
    response = service.select_crop(db, FARM_ID, FARMER_ID, CROP_ID, None, None, None,
                                   None, None, None, "BDT")
    assert response.status == "planned"
    assert active.status == "active"
    assert not any(isinstance(row, RecommendationRecord) for row in db.added)


def test_season_activation_preserves_module3_stage_state_and_rejects_duplicate_active():
    season = SimpleNamespace(id=SEASON_ID, farmland_id=FARM_ID, status="planned",
        current_growth_stage_id=None, crop_id=CROP_ID, crop_variety_id=None, variety_name=None,
        planting_date=None, expected_harvest_date=None, budget_amount=None,
        budget_currency="BDT", actual_harvest_date=None, actual_yield=None,
        yield_unit=None, outcome_notes=None, created_at=None, updated_at=None)
    plan = SimpleNamespace(id=uuid4(), season_id=SEASON_ID, status="draft")
    stage = SimpleNamespace(id=uuid4(), season_plan_id=plan.id, sequence=1)
    db = MemorySession(objects={(Season, SEASON_ID): season}, scalar_results=[plan, stage, None])
    result = service.activate_season(db, SEASON_ID)
    assert result.status == "active"
    assert season.current_growth_stage_id is None
    assert plan.status == "active"

    season.status = "planned"
    db.scalar_results = [plan, stage, SimpleNamespace(id=uuid4())]
    with pytest.raises(service.M2ConflictError, match="already active"):
        service.activate_season(db, SEASON_ID)


def test_plan_generation_orders_stages_and_emits_m3_task_definitions_only():
    season = SimpleNamespace(id=SEASON_ID, farmland_id=FARM_ID, crop_id=CROP_ID,
                             crop_variety_id=None, status="planned", planting_date=None,
                             budget_amount=None)
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID, country_code="BD",
        division=None, district=None, upazila=None, village_or_locality=None,
        latitude=None, longitude=None, land_area_sqm=Decimal("100"), soil_type=None,
        irrigation_available=None, water_source=None, farming_method=None)
    knowledge = synthetic_knowledge(category="season_plan", content={
        "growth_stages": [
            {"name": "Synthetic later stage", "sequence": 2, "start_day": 5, "end_day": 8},
            {"name": "Synthetic first stage", "sequence": 1, "start_day": 0, "end_day": 4},
        ],
        "initial_tasks": [{"title": "Synthetic task definition", "growth_stage_sequence": 1,
                           "due_day_offset": 2}],
    })
    db = MemorySession(objects={(Season, SEASON_ID): season, (Farmland, FARM_ID): farmland})
    with patch.object(service, "_approved_knowledge", return_value=[knowledge]):
        plan = service.create_season_plan(
            db, SEASON_ID, SeasonPlanCreate(season_id=SEASON_ID, title="Synthetic plan")
        )

    assert [stage.sequence for stage in plan.growth_stages] == [1, 2]
    assert plan.initial_tasks[0].growth_stage_id == plan.growth_stages[0].growth_stage_id
    assert not any(isinstance(row, Task) for row in db.added)


def test_active_season_cannot_create_a_draft_that_shadows_its_m3_plan():
    season = SimpleNamespace(
        id=SEASON_ID,
        farmland_id=FARM_ID,
        crop_id=CROP_ID,
        crop_variety_id=None,
        status="active",
    )
    farmland = SimpleNamespace(
        id=FARM_ID,
        farmer_id=FARMER_ID,
        country_code="BD",
        division=None,
        district=None,
        upazila=None,
        village_or_locality=None,
        latitude=None,
        longitude=None,
        land_area_sqm=Decimal("100"),
        soil_type=None,
        irrigation_available=None,
        water_source=None,
        farming_method=None,
    )
    plan_knowledge = synthetic_knowledge(
        category="season_plan",
        content={"growth_stages": [{"name": "TEST ONLY stage", "sequence": 1}]},
    )
    db = MemorySession(objects={(Season, SEASON_ID): season, (Farmland, FARM_ID): farmland})

    with patch.object(service, "_approved_knowledge", return_value=[plan_knowledge]):
        with pytest.raises(service.M2ConflictError, match="active season plan"):
            service.create_season_plan(
                db,
                SEASON_ID,
                SeasonPlanCreate(season_id=SEASON_ID, title="TEST ONLY replacement"),
            )


def test_read_plan_uses_variety_specific_knowledge_for_its_task_definitions():
    variety_id = uuid4()
    plan = SimpleNamespace(id=uuid4(), season_id=SEASON_ID, title="TEST ONLY plan",
                           description=None, status="draft", created_at=None, updated_at=None)
    season = SimpleNamespace(
        id=SEASON_ID,
        farmland_id=FARM_ID,
        crop_id=CROP_ID,
        crop_variety_id=variety_id,
        planting_date=None,
    )
    farmland = SimpleNamespace(
        id=FARM_ID,
        farmer_id=FARMER_ID,
        country_code="BD",
        division=None,
        district=None,
        upazila=None,
        village_or_locality=None,
        latitude=None,
        longitude=None,
        land_area_sqm=Decimal("100"),
        soil_type="synthetic loam",
        irrigation_available=True,
        water_source=None,
        farming_method=None,
    )
    stage = SimpleNamespace(
        id=uuid4(), season_plan_id=plan.id, name="Synthetic stage", description=None,
        sequence=1, start_day=0, end_day=10,
    )
    general = synthetic_knowledge(
        category="season_plan",
        content={"growth_stages": [], "initial_tasks": [{
            "title": "TEST ONLY generic task", "growth_stage_sequence": 1,
            "due_day_offset": 1,
        }]},
    )
    variety_specific = synthetic_knowledge(
        category="season_plan",
        crop_variety_id=variety_id,
        content={"growth_stages": [], "initial_tasks": [{
            "title": "TEST ONLY variety task", "growth_stage_sequence": 1,
            "due_day_offset": 2,
        }]},
    )
    db = MemorySession(
        objects={(Season, SEASON_ID): season, (Farmland, FARM_ID): farmland},
        scalar_results=[plan],
        scalars_result=[stage],
    )

    with patch.object(service, "_approved_knowledge", return_value=[general, variety_specific]):
        response = service.get_season_plan(db, SEASON_ID)

    assert response.initial_tasks[0].title == "TEST ONLY variety task"
    assert response.knowledge_refs[0].knowledge_id == variety_specific.id


def test_farm_today_uses_the_bangladesh_calendar_date():
    class FixedClock:
        @staticmethod
        def now(tz):
            return datetime(2026, 10, 6, 20, tzinfo=timezone.utc).astimezone(tz)

    with patch.object(service, "datetime", FixedClock):
        assert service._farm_today() == date(2026, 10, 7)


def test_empty_plan_stages_are_rejected_without_fabrication():
    season = SimpleNamespace(id=SEASON_ID, farmland_id=FARM_ID, crop_id=CROP_ID,
                             crop_variety_id=None, status="planned", planting_date=None,
                             budget_amount=None)
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID, country_code="BD",
        division=None, district=None, upazila=None, village_or_locality=None,
        latitude=None, longitude=None, land_area_sqm=Decimal("100"), soil_type=None,
        irrigation_available=None, water_source=None, farming_method=None)
    with patch.object(service, "_approved_knowledge", return_value=[synthetic_knowledge(
        category="season_plan", content={"growth_stages": []})]):
        with pytest.raises(service.M2ConflictError, match="no growth_stages"):
            service.create_season_plan(
                MemorySession(objects={(Season, SEASON_ID): season, (Farmland, FARM_ID): farmland}),
                SEASON_ID, SeasonPlanCreate(season_id=SEASON_ID, title="Synthetic plan"),
            )


def test_harvest_guidance_and_missing_knowledge():
    season = SimpleNamespace(id=SEASON_ID, farmland_id=FARM_ID, crop_id=CROP_ID,
                             crop_variety_id=None, planting_date=None)
    farmland = SimpleNamespace(id=FARM_ID, farmer_id=FARMER_ID, country_code="BD",
        division=None, district=None, upazila=None, village_or_locality=None,
        latitude=None, longitude=None, land_area_sqm=Decimal("100"), soil_type=None,
        irrigation_available=None, water_source=None, farming_method=None)
    db = MemorySession(objects={(Season, SEASON_ID): season, (Farmland, FARM_ID): farmland})
    row = synthetic_knowledge(category="harvest_guidance", content={
        "maturity_indicators": ["Synthetic indicator"], "guidance": ["Synthetic test only"]
    })
    with patch.object(service, "_approved_knowledge", return_value=[row]):
        guidance = service.get_harvest_guidance(db, SEASON_ID)
        assert guidance.guidance == ["Synthetic test only"]
        assert guidance.knowledge_refs[0].source_reference == "unit-test-only"
    with patch.object(service, "_approved_knowledge", return_value=[]):
        with pytest.raises(service.M2ConflictError, match="No approved harvest guidance"):
            service.get_harvest_guidance(db, SEASON_ID)


def test_outcome_recording_and_season_history():
    season = SimpleNamespace(id=SEASON_ID, farmland_id=FARM_ID, crop_id=CROP_ID,
        crop_variety_id=None, planting_date=date(2026, 10, 1), expected_harvest_date=None,
        variety_name=None, budget_amount=None, budget_currency="BDT",
        current_growth_stage_id=None, actual_harvest_date=None, actual_yield=None,
        yield_unit=None, outcome_notes=None,
        status="active", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db = MemorySession(objects={(Season, SEASON_ID): season})
    response = service.close_season(db, SeasonOutcomeInput(
        season_id=SEASON_ID, actual_harvest_date=date(2027, 1, 1),
        actual_yield=Decimal("8.5"), yield_unit="kg", outcome_notes="Synthetic test outcome",
    ))
    assert response.status == "completed"
    assert response.actual_yield == Decimal("8.5")

    with pytest.raises(ValueError, match="must not precede"):
        service.close_season(db, SeasonOutcomeInput(
            season_id=SEASON_ID, actual_harvest_date=date(2026, 9, 1),
        ))

    farmland = SimpleNamespace(id=FARM_ID)
    history_db = MemorySession(objects={(Farmland, FARM_ID): farmland}, scalars_result=[season])
    assert service.list_seasons(history_db, FARM_ID)[0].season_id == SEASON_ID


def test_planned_season_cannot_be_closed_before_activation():
    season = SimpleNamespace(
        id=SEASON_ID, farmland_id=FARM_ID, crop_id=CROP_ID,
        crop_variety_id=None, planting_date=date(2026, 10, 1),
        expected_harvest_date=None, status="planned",
        actual_harvest_date=None, actual_yield=None, yield_unit=None,
        outcome_notes=None,
    )
    db = MemorySession(objects={(Season, SEASON_ID): season})

    with pytest.raises(service.M2ConflictError, match="Only active seasons can be closed"):
        service.close_season(db, SeasonOutcomeInput(
            season_id=SEASON_ID, actual_yield=Decimal("12"), status="completed",
        ))
