"""Farmer-facing NASA planting-window evidence response."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OnsetPeriodEvidence(BaseModel):
    years: list[int]
    onset_day_offsets: list[int]
    median_onset_day: float | None
    excluded_years: list[int]
    missing_coverage_years: list[int]
    truncated_confirmation_years: list[int] = Field(default_factory=list)
    no_usable_onset_years: list[int]
    sample_size: int


class MannWhitneyEvidence(BaseModel):
    u_statistic: float | None
    p_value: float | None
    rank_biserial_effect: float | None


class OnsetSensitivityEvidence(BaseModel):
    threshold_mm: float
    status: Literal["available", "insufficient_data"]
    baseline_median_onset_day: float | None
    recent_median_onset_day: float | None
    observed_shift_days: float | None
    baseline_sample_size: int
    recent_sample_size: int


class AnnualOnsetComparisonEvidence(BaseModel):
    status: Literal["available", "insufficient_data"]
    definition: dict[str, int | str]
    baseline_period: str | None
    recent_period: str | None
    baseline: OnsetPeriodEvidence
    recent: OnsetPeriodEvidence
    observed_shift_days: float | None
    mann_whitney: MannWhitneyEvidence
    sensitivity: list[OnsetSensitivityEvidence]
    limitation: str


class AnnualGddEvidence(BaseModel):
    year: int
    total_degree_days: float | None
    valid_days: int
    expected_days: int


class GddEvidence(BaseModel):
    method: str
    annual_values: list[AnnualGddEvidence]
    valid_year_count: int
    baseline_valid_years: int
    recent_valid_years: int
    baseline_mean: float | None
    recent_mean: float | None


class ClimateCoverageEvidence(BaseModel):
    variable: str
    units: str
    status: Literal["available", "partial", "unavailable"]
    expected_observations: int
    valid_observations: int
    missing_observations: int


class DataProvenanceEvidence(BaseModel):
    source: str
    source_url: str
    dataset: str
    variables: list[str]
    temporal_start: date
    temporal_end: date
    spatial_resolution_m: int
    spatial_scale: str
    cache_status: str
    retrieved_at: datetime | None
    district_code: str | None = None
    coverage_by_variable: list[ClimateCoverageEvidence] | None = None
    sampling_point: dict[str, Any] | None = None


class MonthDayWindow(BaseModel):
    start: str = Field(pattern=r"^\d{2}-\d{2}$")
    end: str = Field(pattern=r"^\d{2}-\d{2}$")

    @model_validator(mode="after")
    def validate_dates(self):
        for value in (self.start, self.end):
            month, day = map(int, value.split("-"))
            date(2000, month, day)
        return self


class CalendarDayRange(BaseModel):
    min: int = Field(ge=0)
    max: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.max < self.min:
            raise ValueError("day range must be ordered")
        return self


class CalendarCareReference(BaseModel):
    kind: str
    timing_basis: Literal["days_after_transplanting", "observed_conditions", "observed_stage"]
    day_range: CalendarDayRange | None = None
    condition_en: str
    condition_bn: str | None = None
    detail_en: str
    detail_bn: str | None = None


class CalendarGddReference(BaseModel):
    status: Literal["not_cultivar_validated"]
    reviewed_base_temperature_c: None = None
    cap_temperature_c: None = None
    target_degree_days: None = None
    candidate_method_reference_id: str | None = None


class VarietyCalendarReference(BaseModel):
    profile_id: str | None = None
    variety_name: str
    variety_name_bn: str | None = None
    season: str
    cultivation_method: Literal["transplanted"] = "transplanted"
    review_status: Literal["source_verified_pending_agronomy_review"] = "source_verified_pending_agronomy_review"
    activation_allowed: Literal[False] = False
    seedbed_window: MonthDayWindow | None = None
    seedling_age_days: CalendarDayRange | None = None
    transplanting_window: MonthDayWindow
    reported_life_duration_days: int
    harvest_window: MonthDayWindow
    duration_reference_event: Literal["not_stated"] = "not_stated"
    care_references: list[CalendarCareReference] = Field(default_factory=list)
    gdd_reference: CalendarGddReference | None = None
    excluded_ambiguities: list[str] = Field(default_factory=list)
    geographic_scope_bn: str
    geographic_scope_en: str
    source_name: str
    source_url: str
    source_accessed: date
    limitations_bn: list[str]
    limitations_en: list[str]


class PlantingWindowEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["available", "insufficient_data", "unavailable"]
    message_bn: str
    message_en: str
    farmland_id: str
    season_id: str
    crop_name: str
    annual_comparison: AnnualOnsetComparisonEvidence | None = None
    recommended_shift_days: float | None = None
    gdd_summary: GddEvidence | None = None
    planting_calendar: dict[str, Any] | None = None
    variety_calendar_reference: VarietyCalendarReference | None = None
    data_provenance: DataProvenanceEvidence
    limitations_bn: list[str]
    limitations_en: list[str]


class DistrictClimateEvidence(BaseModel):
    status: Literal["provisional", "insufficient_data"]
    definition_review_status: Literal["exploratory_pending_review"] = "exploratory_pending_review"
    annual_comparison: AnnualOnsetComparisonEvidence
    data_provenance: DataProvenanceEvidence
    limitations_bn: list[str]
    limitations_en: list[str]


class PublicPlantingWindowEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["needs_selection", "provisional", "insufficient_data"]
    district_code: str
    district_name: str
    district_name_bn: str
    crop_code: Literal["rice"] = "rice"
    season: str | None = None
    season_choices: list[str] = Field(default_factory=lambda: ["aman", "aus", "boro"])
    message_bn: str
    message_en: str
    sms_bn: str = Field(max_length=159)
    sms_en: str = Field(max_length=159)
    definition_review_status: Literal["exploratory_pending_review"] = "exploratory_pending_review"
    annual_comparison: AnnualOnsetComparisonEvidence | None = None
    recommended_shift_days: None = None
    gdd_summary: None = None
    calendar_references: list[VarietyCalendarReference] = Field(default_factory=list)
    data_provenance: DataProvenanceEvidence | None = None
    limitations_bn: list[str] = Field(default_factory=list)
    limitations_en: list[str] = Field(default_factory=list)


def unavailable_provenance(*, cache_status: str = "not_requested") -> dict[str, Any]:
    return {
        "source": "NASA POWER Daily Point",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "dataset": "POWER Daily API, community AG",
        "variables": ["precipitation (mm/day)", "temperature (°C)", "solar radiation (MJ/m²/day)"],
        "temporal_start": date(2001, 1, 1),
        "temporal_end": date(2025, 12, 31),
        "spatial_resolution_m": 50000,
        "spatial_scale": "area-level grid, approximately 50 km; not field-level",
        "cache_status": cache_status,
        "retrieved_at": None,
    }


class DistrictCacheEntry(BaseModel):
    """Local index presence only; selected evidence still requires validation."""

    model_config = ConfigDict(extra="forbid")
    district_code: str = Field(pattern=r"^\d{4}$")
    name: str
    name_bn: str
    status: Literal["cached", "missing", "unreadable"]


class DistrictCacheInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    districts: list[DistrictCacheEntry] = Field(max_length=64)
    cached_count: int = Field(ge=0, le=64)
    requires_validation_on_load: Literal[True] = True
