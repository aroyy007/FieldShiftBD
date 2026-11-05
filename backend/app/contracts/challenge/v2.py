"""Regional comparison contracts; v1 consumers retain their original semantics."""
from __future__ import annotations
from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

Priority = Literal['water', 'calendar', 'rainfall', 'diversity', 'income']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class RotationCompareRequest(StrictModel):
    planning_year: int = Field(ge=2001, le=2040)
    priorities: list[Priority] = Field(default_factory=lambda: ['water', 'calendar'], min_length=1, max_length=5)

    @model_validator(mode='after')
    def unique_priorities(self):
        if len(set(self.priorities)) != len(self.priorities):
            raise ValueError('Priorities must be unique and ordered')
        return self


class MetricEvidence(StrictModel):
    metric_id: str
    status: Literal['available', 'partial', 'missing', 'not_applicable']
    value: float | None = None
    unit: str | None = None
    method_id: str
    evidence_ids: list[str]
    valid_year_count: int = Field(default=0, ge=0)
    total_year_count: int = Field(default=0, ge=0)
    detail_en: str = ''
    detail_bn: str = ''

    @model_validator(mode='after')
    def truthful_value(self):
        if self.status in ('missing', 'not_applicable') and self.value is not None:
            raise ValueError('Missing/not-applicable metrics cannot contain numeric values')
        if self.valid_year_count > self.total_year_count:
            raise ValueError('Valid years cannot exceed total years')
        return self


class ProductDefinition(StrictModel):
    product_id: str
    short_name: str
    version: str
    url: str
    role: Literal['decision', 'corroboration', 'context_only', 'conditional_context']
    kind: Literal['retrieval', 'reanalysis', 'assimilation', 'model_output', 'static_surface']
    native_support: str
    shared_input_groups: list[str] = Field(default_factory=list)
    limitations: str


class RegionDefinition(StrictModel):
    code: Literal['5081', '2015']
    name_en: str
    name_bn: str
    area_status: Literal['boundary_required', 'verified_boundary'] = 'boundary_required'


class EvidenceReference(StrictModel):
    evidence_id: str
    source: str
    product_id: str
    version: str
    url: str
    role: str
    spatial_support: str
    coverage_start: date | None = None
    coverage_end: date | None = None
    retrieved_at: str | None = None
    checksum_sha256: str | None = None
    cache_status: Literal['hit', 'missing', 'corrupt', 'not_acquired']
    scope: Literal['reference_point', 'regional_grid', 'regional_context', 'published_agronomy']


class CalendarWindowV2(StrictModel):
    start: str
    end: str


class CalendarWeatherV2(StrictModel):
    status: Literal['available', 'insufficient_data']
    establishment_start: date
    establishment_end: date
    harvest_start: date
    harvest_end: date
    short_interval_median_mm: float | None
    long_interval_median_mm: float | None
    short_interval_dry_spell_median_days: float | None = None
    long_interval_dry_spell_median_days: float | None = None
    valid_year_count: int
    total_year_count: int
    method_id: str


class CalendarReferenceV2(StrictModel):
    profile_id: str
    variety_name: str
    variety_name_bn: str
    cultivation_method: str
    establishment_window: CalendarWindowV2
    harvest_window: CalendarWindowV2
    source_url: str
    source_id: str
    accessed_on: date
    scope_en: str
    scope_bn: str
    review_status: Literal['source_verified_pending_agronomy_review'] = 'source_verified_pending_agronomy_review'
    weather: CalendarWeatherV2 | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class CalendarStepEvidenceV2(StrictModel):
    status: Literal['source_reference_available', 'method_mismatch', 'method_not_recorded', 'not_available']
    references: list[CalendarReferenceV2] = Field(default_factory=list)
    limitation_en: str
    limitation_bn: str


class RotationStepV2(StrictModel):
    crop_code: str
    season_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    event_basis: str = 'not_recorded'
    calendar_evidence: CalendarStepEvidenceV2 | None = None


class RotationOptionV2(StrictModel):
    option_id: str
    role: Literal['baseline', 'alternative']
    name_en: str
    name_bn: str
    steps: list[RotationStepV2]
    eligibility: Literal['eligible', 'ineligible', 'unknown']
    reasons_en: list[str] = Field(default_factory=list)
    reasons_bn: list[str] = Field(default_factory=list)
    metrics: list[MetricEvidence] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    benefits_en: list[str] = Field(default_factory=list)
    benefits_bn: list[str] = Field(default_factory=list)
    risks_en: list[str] = Field(default_factory=list)
    risks_bn: list[str] = Field(default_factory=list)


class PilotTerrainV2(StrictModel):
    latitude: float
    longitude: float
    elevation_m: float | None
    source_file: str
    checksum_sha256: str
    acquisition_method: Literal['user_supplied_unverified']
    acquisition_date: str
    product: str
    native_support: str
    sample_basis: Literal['field_profile_coordinate']


class PilotObservationV2(StrictModel):
    status: Literal['prototype_unreviewed']
    date: date
    mean_mm: float
    coverage_fraction: float
    native_support_count: int
    bbox_wgs84: list[float]
    source: str
    acquisition_method: Literal['user_supplied_unverified']
    source_url: str
    native_support: str
    release_id: str
    terrain: PilotTerrainV2 | None = None


class RotationComparisonV2(StrictModel):
    contract_version: Literal['2.0.0'] = '2.0.0'
    farmland_id: UUID
    district_code: str | None
    planning_year: int
    snapshot_hash: str
    release_id: str | None = None
    status: Literal['available', 'partial', 'insufficient_evidence', 'unsupported_region']
    baseline_completeness: Literal['complete', 'incomplete', 'not_recorded']
    priorities: list[Priority]
    ordering_status: Literal['ordered', 'tied', 'insufficient_evidence'] = 'insufficient_evidence'
    preferred_option_ids: list[str] = Field(default_factory=list)
    options: list[RotationOptionV2] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    products: list[dict[str, str]] = Field(default_factory=list)
    message_en: str
    message_bn: str
    limitations_en: list[str] = Field(default_factory=list)
    limitations_bn: list[str] = Field(default_factory=list)
    selection_allowed: Literal[False] = False
    recommended_shift_days: None = None
    pilot_observation: PilotObservationV2 | None = None
