"""Farmer-facing NASA planting-window evidence response."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class OnsetPeriodEvidence(BaseModel):
    years: list[int]
    onset_day_offsets: list[int]
    median_onset_day: float | None
    excluded_years: list[int]
    missing_coverage_years: list[int]
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
    data_provenance: DataProvenanceEvidence
    limitations_bn: list[str]
    limitations_en: list[str]


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
