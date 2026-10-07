"""API/domain schemas for Module 2: Crop Advisor & Season Lifecycle.

These schemas describe M2 inputs and outputs. They do not define persistence
models; persisted farm, crop, and season records remain in ``app.models``.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)


class M2Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", check_fields=False, when_used="json")
    def serialize_decimal_values(self, value: Any) -> Any:
        """Emit JSON numbers for Decimal fields, matching the mobile API types."""
        return float(value) if isinstance(value, Decimal) else value


MAX_SEASON_BUDGET = Decimal("999999999999.99")
MAX_SEASON_YIELD = Decimal("99999999999.999")


class LandAreaUnit(StrEnum):
    SQUARE_METRE = "square_metre"
    DECIMAL = "decimal"
    ACRE = "acre"
    HECTARE = "hectare"


class SeasonStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RecommendationStatus(StrEnum):
    PROPOSED = "proposed"
    SELECTED = "selected"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class RecommendationSetStatus(StrEnum):
    AVAILABLE = "available"
    NO_APPROVED_KNOWLEDGE = "no_approved_knowledge"
    NO_SUPPORTED_FIT = "no_supported_fit"


class SeasonPlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    COMPLETED = "completed"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskSource(StrEnum):
    SEASON_PLAN = "season_plan"


class FarmLocation(M2Schema):
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    division: str | None = None
    district: str | None = None
    upazila: str | None = None
    village_or_locality: str | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)


class PreviousCropOutcome(M2Schema):
    crop_id: UUID | None = None
    crop_name: str | None = None
    yield_amount: Decimal | None = Field(default=None, ge=0)
    yield_unit: str | None = None
    season_year: int | None = Field(default=None, ge=1900, le=2200)


class FarmResource(M2Schema):
    name: str
    quantity: Decimal | None = Field(default=None, ge=0)
    unit: str | None = None
    notes: str | None = None


class FarmProfileInput(M2Schema):
    """M1 → M2 profile contract, composed from farmer and farmland data."""

    farmer_id: UUID | None = None
    farmland_id: UUID | None = None
    location: FarmLocation | None = None
    land_area: Decimal | None = Field(default=None, gt=0)
    land_unit: LandAreaUnit | None = None
    land_area_sqm: Decimal | None = Field(default=None, gt=0)
    soil_type: str | None = None
    irrigation_available: bool | None = None
    water_source: str | None = None
    previous_crop: PreviousCropOutcome | None = None
    previous_yield: Decimal | None = Field(default=None, ge=0)
    equipment: list[str] = Field(default_factory=list)
    farming_experience_years: Decimal | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("farming_experience", "farming_experience_years"),
        serialization_alias="farming_experience",
    )
    farming_method: str | None = None
    budget_amount: Decimal | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("budget", "budget_amount"),
        serialization_alias="budget",
    )
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3)
    resources: list[FarmResource] = Field(default_factory=list)
    crop_preferences: list[UUID] = Field(default_factory=list)
    livestock: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reconcile_previous_yield(self) -> Self:
        nested_yield = self.previous_crop.yield_amount if self.previous_crop else None
        if self.previous_yield is None and nested_yield is not None:
            self.previous_yield = nested_yield
        elif nested_yield is not None and self.previous_yield != nested_yield:
            raise ValueError("previous_yield conflicts with previous_crop.yield_amount")
        return self


class CropIdentity(M2Schema):
    crop_id: UUID
    name: str | None = None
    scientific_name: str | None = None


class CropVarietyIdentity(M2Schema):
    crop_variety_id: UUID | None = None
    name: str | None = None


class KnowledgeReference(M2Schema):
    knowledge_id: UUID | None = None
    source_name: str
    source_type: str | None = None
    source_reference: str | None = None
    category: str | None = None
    region_code: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    review_status: str | None = None
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    acceptance_method: str | None = None


class SuitabilityFactor(M2Schema):
    factor: str
    explanation: str
    knowledge_refs: list[KnowledgeReference] = Field(default_factory=list)


class RecommendationReasoning(M2Schema):
    summary: str | None = None
    positive_factors: list[SuitabilityFactor] = Field(default_factory=list)
    limiting_factors: list[SuitabilityFactor] = Field(default_factory=list)
    risks_or_concerns: list[SuitabilityFactor] = Field(default_factory=list)


class CropRecommendation(M2Schema):
    recommendation_id: UUID | None = None
    farmland_id: UUID
    crop: CropIdentity
    score: Decimal | None = Field(default=None, ge=0, le=1)
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    reasoning: RecommendationReasoning
    knowledge_refs: list[KnowledgeReference] = Field(default_factory=list)


class CropRecommendationSet(M2Schema):
    farmland_id: UUID
    status: RecommendationSetStatus
    message: str
    recommendations: list[CropRecommendation] = Field(default_factory=list)


class CropSelectionInput(M2Schema):
    farmer_id: UUID | None = None
    farmland_id: UUID
    crop_id: UUID
    crop_variety_id: UUID | None = None
    variety_name: str | None = None
    recommendation_id: UUID | None = None
    selected_at: datetime | None = None
    notes: str | None = None


class CropSelectionRequest(CropSelectionInput):
    """M2 endpoint payload; adds season setup fields without changing shared contracts."""

    planting_date: date | None = None
    expected_harvest_date: date | None = None
    budget_amount: Decimal | None = Field(default=None, ge=0, le=MAX_SEASON_BUDGET)
    budget_currency: str = Field(default="BDT", min_length=3, max_length=3)

    @model_validator(mode="after")
    def expected_harvest_not_before_planting(self) -> Self:
        if (
            self.planting_date is not None
            and self.expected_harvest_date is not None
            and self.expected_harvest_date < self.planting_date
        ):
            raise ValueError("expected_harvest_date must not precede planting_date")
        return self


class SeasonCreate(M2Schema):
    farmland_id: UUID
    crop_id: UUID
    crop_variety_id: UUID | None = None
    variety_name: str | None = None
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    status: SeasonStatus = SeasonStatus.PLANNED
    budget_amount: Decimal | None = Field(default=None, ge=0, le=MAX_SEASON_BUDGET)
    budget_currency: str = Field(default="BDT", min_length=3, max_length=3)

    @model_validator(mode="after")
    def expected_harvest_not_before_planting(self) -> Self:
        if (
            self.planting_date is not None
            and self.expected_harvest_date is not None
            and self.expected_harvest_date < self.planting_date
        ):
            raise ValueError("expected_harvest_date must not precede planting_date")
        return self


class SeasonResponse(SeasonCreate):
    season_id: UUID
    actual_harvest_date: date | None = None
    actual_yield: Decimal | None = Field(default=None, ge=0, le=MAX_SEASON_YIELD)
    yield_unit: str | None = None
    outcome_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SeasonPlanCreate(M2Schema):
    season_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: SeasonPlanStatus = SeasonPlanStatus.DRAFT


class GrowthStageDefinition(M2Schema):
    growth_stage_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    sequence: int = Field(gt=0)
    start_day: int | None = Field(default=None, ge=0)
    end_day: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def end_not_before_start(self) -> Self:
        if (
            self.start_day is not None
            and self.end_day is not None
            and self.end_day < self.start_day
        ):
            raise ValueError("end_day must be greater than or equal to start_day")
        return self


class InitialTaskDefinition(M2Schema):
    """M2 plan output for M3; contains no operational task state."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    due_day_offset: int | None = Field(default=None, ge=0)
    priority: TaskPriority = TaskPriority.NORMAL
    source: TaskSource = TaskSource.SEASON_PLAN
    growth_stage_id: UUID | None = None
    growth_stage_sequence: int | None = Field(default=None, gt=0)


class SeasonPlanResponse(SeasonPlanCreate):
    season_plan_id: UUID
    growth_stages: list[GrowthStageDefinition] = Field(default_factory=list)
    initial_tasks: list[InitialTaskDefinition] = Field(default_factory=list)
    knowledge_refs: list[KnowledgeReference] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HarvestGuidance(M2Schema):
    maturity_indicators: list[str] = Field(default_factory=list)
    recommended_window_start: date | None = None
    recommended_window_end: date | None = None
    guidance: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    knowledge_refs: list[KnowledgeReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def window_end_not_before_start(self) -> Self:
        if (
            self.recommended_window_start is not None
            and self.recommended_window_end is not None
            and self.recommended_window_end < self.recommended_window_start
        ):
            raise ValueError("recommended harvest window end precedes its start")
        return self


class SeasonOutcomeInput(M2Schema):
    season_id: UUID
    outcome_notes: str | None = None
    actual_yield: Decimal | None = Field(default=None, ge=0, le=MAX_SEASON_YIELD)
    yield_unit: str | None = None
    actual_harvest_date: date | None = None
    status: SeasonStatus | None = None


class SeasonOutcomeResponse(SeasonOutcomeInput):
    farmland_id: UUID
    crop_id: UUID
    crop_variety_id: UUID | None = None
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
