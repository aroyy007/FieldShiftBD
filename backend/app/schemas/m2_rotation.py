"""Contracts for read-only Module 2 crop rotation comparisons."""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.m2_advisor import M2Schema


class RotationPriority(StrEnum):
    FEWER_FALLOW_SLOTS = "fewer_fallow_slots"
    INCLUDE_LEGUME = "include_legume"
    MORE_CROP_TYPES = "more_crop_types"
    MATCH_FARM_CONTEXT = "match_farm_context"


class RotationComparisonRequest(M2Schema):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    priorities: list[RotationPriority] = Field(
        default_factory=lambda: [RotationPriority.MATCH_FARM_CONTEXT],
        min_length=1,
        max_length=4,
    )


class RotationSource(M2Schema):
    source_name: str
    source_reference: str
    claim: str | None = None
    limitation: str | None = None


class RotationPattern(M2Schema):
    pattern_id: str
    sequence: list[str]
    crop_slots: int = Field(ge=0)
    distinct_crop_types: int = Field(ge=0)
    fallow_slots: int = Field(ge=0)
    contains_legume: bool
    fit_status: Literal[
        "matches_published_conditions",
        "not_published_conditions",
        "not_current_source_crop",
        "source_variety_not_confirmed",
        "farm_context_incomplete",
    ]
    fit_notes: list[str]
    priority_matches: list[RotationPriority]
    sequence_notes: list[str]
    source: RotationSource


class RotationClimateAnnualValue(M2Schema):
    year: int
    rainfall_total_mm: float
    mean_temperature_c: float
    days_observed: int
    days_expected: int
    coverage_percent: float


class RotationClimatePeriod(M2Schema):
    start_year: int
    end_year: int
    years_observed: int
    years_available: int
    mean_annual_rainfall_mm: float | None
    mean_annual_temperature_c: float | None
    observed_days: int
    expected_days: int
    coverage_percent: float
    annual_values: list[RotationClimateAnnualValue]


class RotationClimateDifference(M2Schema):
    annual_rainfall_mm: float | None
    annual_mean_temperature_c: float | None


class RotationClimateComparison(M2Schema):
    earlier: RotationClimatePeriod
    later: RotationClimatePeriod
    difference_later_minus_earlier: RotationClimateDifference


class RotationClimateMonthDifference(M2Schema):
    rainfall_mm: float | None
    temperature_c: float | None


class RotationClimateMonthPeriod(M2Schema):
    years_observed: int
    years_available: int
    mean_monthly_rainfall_mm: float | None
    mean_temperature_c: float | None
    observed_days: int
    expected_days: int
    coverage_percent: float


class RotationClimateMonth(M2Schema):
    month: int
    earlier: RotationClimateMonthPeriod
    later: RotationClimateMonthPeriod
    difference_later_minus_earlier: RotationClimateMonthDifference


class RotationClimateContext(M2Schema):
    dataset: str
    source_reference: str
    resolution_reference: str
    time_standard: str
    parameters: list[dict[str, str]]
    observation_scale: str
    retrieved_at: str | None
    cache_status: Literal["live", "live_uncached", "disk_cache", "stale_cache", "unavailable"]
    requested_period: dict[str, str] | None
    observed_period: dict[str, str | None] | None
    annual_values: list[RotationClimateAnnualValue]
    period_comparison: RotationClimateComparison | None
    monthly_comparison: list[RotationClimateMonth]
    unavailable_reason: str | None = None
    requested_coordinate: dict[str, float] | None = None
    query_coordinate: dict[str, float] | None = None


class RotationComparisonResponse(M2Schema):
    farmland_id: UUID
    status: Literal["available", "profile_incomplete", "no_supported_patterns"]
    priority_order: list[RotationPriority]
    current_crop: str | None = None
    current_variety: str | None = None
    previous_crop: str | None = None
    patterns: list[RotationPattern]
    additional_evidence: list[RotationSource]
    limitations: list[str]
    climate_context: RotationClimateContext
