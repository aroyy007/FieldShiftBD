"""Stable, versioned seams shared by the six FieldShift modules.

These are transport and persistence contracts only. They do not implement
agronomic recommendations, climate retrieval, disease inference, or speech.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = "1.0.0"

DistrictCode = str
CropCode = str
SourceMethod = Literal[
    "farmer_input",
    "nasa_power",
    "imerg",
    "smap",
    "modis_ndvi",
    "landsat",
    "ecostress",
    "grace_fo",
    "srtm",
    "gedi",
    "nex_gddp_cmip6",
    "bam_derived",
    "third_party",
    "model_output",
    "human_review",
    "manual_entry",
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContractCatalog(ContractModel):
    """Root used by the deterministic JSON Schema/TypeScript exporter."""

    contract_version: Literal["1.0.0"]
    source_provenance: "SourceProvenance | None" = None
    farm_profile_snapshot: "FarmProfileSnapshot | None" = None
    district_climate_bundle_manifest: "DistrictClimateBundleManifest | None" = None
    district_climate_bundle: "DistrictClimateBundle | None" = None
    climate_variable_coverage: "ClimateVariableCoverage | None" = None
    planting_window_advisory: "PlantingWindowAdvisory | None" = None
    rotation_comparison: "RotationComparison | None" = None
    adaptive_recommendation: "AdaptiveRecommendation | None" = None
    proposed_action: "ProposedAction | None" = None
    task_diff: "TaskDiff | None" = None
    task_diff_apply_result: "TaskDiffApplyResult | None" = None
    action_execution_receipt: "ActionExecutionReceipt | None" = None
    consent_record_input: "ConsentRecordInput | None" = None
    disease_problem_sync_request: "DiseaseProblemSyncRequest | None" = None
    disease_problem_sync_receipt: "DiseaseProblemSyncReceipt | None" = None
    api_error: "ApiError | None" = None


class SourceProvenance(ContractModel):
    source_id: str = Field(min_length=1, max_length=200)
    source_name: str = Field(min_length=1, max_length=200)
    source_url: str | None = Field(default=None, max_length=2048)
    dataset_version: str | None = Field(default=None, max_length=120)
    retrieved_at: AwareDatetime
    recorded_at: AwareDatetime
    method: SourceMethod
    license: str | None = Field(default=None, max_length=240)
    checksum_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    temporal_start: date | None = None
    temporal_end: date | None = None
    spatial_resolution_m: float | None = Field(default=None, gt=0)
    quality_status: Literal[
        "verified", "provisional", "synthetic", "stale", "unavailable"
    ] = "verified"

    @model_validator(mode="after")
    def validate_temporal_coverage(self) -> "SourceProvenance":
        if (
            self.temporal_start is not None
            and self.temporal_end is not None
            and self.temporal_end < self.temporal_start
        ):
            raise ValueError("temporal_end must not precede temporal_start")
        return self


class FarmlandProfile(ContractModel):
    country_code: Literal["BD"] = "BD"
    division: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    district_code: DistrictCode | None = Field(default=None, max_length=24)
    upazila: str | None = Field(default=None, max_length=120)
    upazila_code: str | None = Field(default=None, max_length=32)
    village_or_locality: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    land_area_sqm: float = Field(gt=0)
    area_unit: Literal["square_metre", "decimal", "acre", "hectare"]
    soil_type: str | None = Field(default=None, max_length=120)
    land_type: str | None = Field(default=None, max_length=120)
    irrigation_available: bool | None = None
    water_source: str | None = Field(default=None, max_length=120)
    equipment: list[str] = Field(default_factory=list, max_length=100)
    budget_amount: float | None = Field(default=None, ge=0)
    budget_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def validate_coordinate_pair(self) -> "FarmlandProfile":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class SeasonSnapshot(ContractModel):
    season_id: UUID
    crop_id: UUID | None = None
    crop_code: CropCode | None = Field(default=None, min_length=1, max_length=80)
    variety_id: UUID | None = None
    variety_name: str | None = Field(default=None, max_length=160)
    status: Literal["planned", "active", "completed", "cancelled"]
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    current_growth_stage_id: UUID | None = None
    current_growth_stage_name: str | None = Field(default=None, max_length=160)
    growth_stage_as_of: date | None = None


class CropPriority(ContractModel):
    crop_code: CropCode = Field(min_length=1, max_length=80)
    rank: int = Field(ge=1, le=100)
    reason: str | None = Field(default=None, max_length=500)


class RotationHistoryEntry(ContractModel):
    season_id: UUID
    crop_code: CropCode = Field(min_length=1, max_length=80)
    planting_date: date | None = None
    harvest_date: date | None = None
    yield_amount: float | None = Field(default=None, ge=0)
    yield_unit: str | None = Field(default=None, max_length=80)
    source: Literal["farmer_reported", "recorded_plan", "verified"]


class FarmProfileSnapshot(ContractModel):
    contract_version: Literal["1.0.0"]
    farmland_id: UUID
    farmer_id: UUID
    captured_at: AwareDatetime
    profile: FarmlandProfile
    active_season: SeasonSnapshot | None = None
    crop_priorities: list[CropPriority] = Field(default_factory=list, max_length=100)
    rotation_history: list[RotationHistoryEntry] = Field(default_factory=list, max_length=100)
    provenance: list[SourceProvenance] = Field(min_length=1, max_length=100)


class ClimateAssetManifest(ContractModel):
    asset_id: str = Field(min_length=1, max_length=200)
    source_name: str = Field(min_length=1, max_length=200)
    dataset_id: str = Field(min_length=1, max_length=160)
    dataset_version: str = Field(min_length=1, max_length=120)
    variable: str = Field(min_length=1, max_length=120)
    units: str = Field(min_length=1, max_length=60)
    spatial_resolution_m: float | None = Field(default=None, gt=0)
    temporal_resolution: Literal["daily", "8_day", "monthly", "static", "scenario"]
    coverage_start: date
    coverage_end: date
    relative_path: str = Field(min_length=1, max_length=500)
    checksum_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0)
    license: str = Field(min_length=1, max_length=240)
    quality_status: Literal["verified", "provisional", "synthetic"]

    @model_validator(mode="after")
    def validate_asset_coverage(self) -> "ClimateAssetManifest":
        if self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end must not precede coverage_start")
        if self.relative_path.startswith(("/", "\\")) or ".." in self.relative_path.replace("\\", "/").split("/"):
            raise ValueError("relative_path must remain inside the configured cache")
        return self


class DistrictClimateBundleManifest(ContractModel):
    contract_version: Literal["1.0.0"]
    district_code: DistrictCode = Field(min_length=1, max_length=24)
    bundle_id: str = Field(min_length=1, max_length=200)
    created_at: AwareDatetime
    expires_at: AwareDatetime | None = None
    coverage_start: date
    coverage_end: date
    assets: list[ClimateAssetManifest] = Field(max_length=100)
    coverage_by_variable: list["ClimateVariableCoverage"] = Field(default_factory=list, max_length=100)
    provenance: list[SourceProvenance] = Field(default_factory=list, max_length=100)
    quality_status: Literal["verified", "provisional", "synthetic"] = "verified"

    @model_validator(mode="after")
    def validate_manifest_coverage(self) -> "DistrictClimateBundleManifest":
        if self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end must not precede coverage_start")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        variables = [item.variable for item in self.coverage_by_variable]
        if len(variables) != len(set(variables)):
            raise ValueError("manifest coverage entries must have unique variable names")
        return self


class DailyClimateObservation(ContractModel):
    date: date
    rainfall_mm: float = Field(ge=0)
    temperature_c: float
    solar_mj_m2_day: float = Field(ge=0)
    quality_flags: list[str] = Field(default_factory=list, max_length=100)


class ClimateVariableCoverage(ContractModel):
    """Measured coverage; unavailable observations are never represented as zero."""

    variable: str = Field(min_length=1, max_length=120)
    units: str = Field(min_length=1, max_length=60)
    status: Literal["available", "partial", "unavailable"]
    expected_observations: int = Field(ge=0)
    valid_observations: int = Field(ge=0)
    missing_observations: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_coverage_counts(self) -> "ClimateVariableCoverage":
        if self.valid_observations + self.missing_observations != self.expected_observations:
            raise ValueError("valid and missing counts must equal expected observations")
        if self.status == "available" and (
            self.expected_observations == 0 or self.missing_observations != 0
        ):
            raise ValueError("available coverage must contain expected complete observations")
        if self.status == "partial" and not (
            self.valid_observations > 0 and self.missing_observations > 0
        ):
            raise ValueError("partial coverage must contain both valid and missing observations")
        if self.status == "unavailable" and self.valid_observations != 0:
            raise ValueError("unavailable coverage cannot claim valid observations")
        return self


class DistrictClimateBundle(ContractModel):
    contract_version: Literal["1.0.0"]
    manifest: DistrictClimateBundleManifest
    daily_series: list[DailyClimateObservation] = Field(min_length=1, max_length=20000)

    @model_validator(mode="after")
    def validate_daily_series(self) -> "DistrictClimateBundle":
        dates = [row.date for row in self.daily_series]
        if dates != sorted(set(dates)):
            raise ValueError("daily series dates must be unique and strictly increasing")
        if dates[0] < self.manifest.coverage_start or dates[-1] > self.manifest.coverage_end:
            raise ValueError("daily series must remain within manifest coverage")
        return self


class OnsetComparison(ContractModel):
    baseline_years: list[int] = Field(min_length=12, max_length=12)
    recent_years: list[int] = Field(min_length=13, max_length=13)
    baseline_onset_days: list[int] = Field(min_length=12, max_length=12)
    recent_onset_days: list[int] = Field(min_length=13, max_length=13)
    test_name: Literal["mann_whitney_u"]
    test_statistic: float = Field(ge=0)
    p_value: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_periods(self) -> "OnsetComparison":
        if self.baseline_years != list(range(2001, 2013)):
            raise ValueError("baseline years must cover 2001 through 2012")
        if self.recent_years != list(range(2013, 2026)):
            raise ValueError("recent years must cover 2013 through 2025")
        if any(day < 1 or day > 366 for day in self.baseline_onset_days + self.recent_onset_days):
            raise ValueError("onset day must be within the calendar year")
        return self


class RecommendedPlantingWindow(ContractModel):
    start: date
    end: date

    @model_validator(mode="after")
    def validate_window(self) -> "RecommendedPlantingWindow":
        if self.end < self.start:
            raise ValueError("window end must not precede its start")
        return self


class PlantingWindowAdvisory(ContractModel):
    contract_version: Literal["1.0.0"]
    status: Literal["available", "insufficient_data", "provisional", "unavailable"]
    district_code: DistrictCode = Field(min_length=1, max_length=24)
    crop_code: CropCode = Field(min_length=1, max_length=80)
    onset_shift_days: int | None = Field(default=None, ge=-366, le=366)
    comparison: OnsetComparison | None = None
    recommended_window: RecommendedPlantingWindow | None = None
    advice_bn: str | None = Field(default=None, max_length=1000)
    advice_en: str | None = Field(default=None, max_length=1000)
    sms_summary: str | None = Field(default=None, max_length=160)
    assumptions: list[str] = Field(default_factory=list, max_length=100)
    provenance: list[SourceProvenance] = Field(default_factory=list, max_length=100)
    created_at: AwareDatetime

    @model_validator(mode="after")
    def validate_available_evidence(self) -> "PlantingWindowAdvisory":
        if self.status == "available" and (
            self.onset_shift_days is None
            or self.comparison is None
            or self.recommended_window is None
            or not self.provenance
        ):
            raise ValueError("available advice requires a shift, comparison, window, and provenance")
        return self


class RotationComparison(ContractModel):
    contract_version: Literal["1.0.0"]
    farmland_id: UUID
    current_sequence: list[CropCode] = Field(min_length=1, max_length=12)
    alternatives: list[list[CropCode]] = Field(min_length=1, max_length=3)
    evidence: list[SourceProvenance] = Field(min_length=1, max_length=100)
    created_at: AwareDatetime


class AdaptiveRecommendation(ContractModel):
    contract_version: Literal["1.0.0"]
    farmland_id: UUID
    decision_question: str = Field(min_length=1, max_length=500)
    answer_status: Literal[
        "recommended", "no_change", "needs_farmer_input", "insufficient_evidence", "unavailable"
    ]
    recommendation_code: str | None = Field(default=None, max_length=120)
    confidence: float | None = Field(default=None, ge=0, le=1)
    constraints: list[str] = Field(default_factory=list, max_length=100)
    unknowns: list[str] = Field(default_factory=list, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    created_at: AwareDatetime

    @model_validator(mode="after")
    def avoid_unsupported_recommendation(self) -> "AdaptiveRecommendation":
        if self.answer_status in {"insufficient_evidence", "unavailable", "needs_farmer_input"}:
            if self.recommendation_code is not None or self.confidence is not None:
                raise ValueError("an unresolved recommendation cannot claim a code or confidence")
        if self.answer_status == "recommended" and not self.evidence_refs:
            raise ValueError("a recommendation requires evidence references")
        return self


class ActionPrecondition(ContractModel):
    kind: Literal[
        "farm_state_matches", "task_state_matches", "evidence_is_fresh", "consent_is_active"
    ]
    subject: str = Field(min_length=1, max_length=200)
    expected_value: Any | None = None
    observed_at: AwareDatetime | None = None
    max_age_seconds: int | None = Field(default=None, ge=0, le=31_536_000)


class TaskDiffOperation(ContractModel):
    operation: Literal["create", "update", "complete", "cancel"]
    reference: str = Field(min_length=1, max_length=200)
    task_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    due_at: AwareDatetime | None = None
    priority: Literal["low", "normal", "high", "urgent"] | None = None
    expected_status: Literal["pending", "completed", "skipped", "cancelled"] | None = None

    @model_validator(mode="after")
    def validate_operation_fields(self) -> "TaskDiffOperation":
        if self.operation == "create" and self.title is None:
            raise ValueError("create operations require a title")
        if self.operation != "create" and self.task_id is None:
            raise ValueError("non-create operations require a task_id")
        if self.operation in {"complete", "cancel"} and self.expected_status not in {None, "pending"}:
            raise ValueError("only a pending task can be completed or cancelled")
        return self


class TaskDiff(ContractModel):
    operations: list[TaskDiffOperation] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def references_are_unique(self) -> "TaskDiff":
        refs = [item.reference for item in self.operations]
        if len(refs) != len(set(refs)):
            raise ValueError("task diff references must be unique")
        return self


class TaskDiffApplyResult(ContractModel):
    """M3-owned, transaction-aware task mutation receipt for M5 orchestration."""

    contract_version: Literal["1.0.0"]
    action_id: UUID
    farmer_id: UUID
    farmland_id: UUID
    season_id: UUID
    created_task_ids: list[UUID] = Field(default_factory=list, max_length=100)
    updated_task_ids: list[UUID] = Field(default_factory=list, max_length=100)
    completed_task_ids: list[UUID] = Field(default_factory=list, max_length=100)
    cancelled_task_ids: list[UUID] = Field(default_factory=list, max_length=100)


class ProposedAction(ContractModel):
    contract_version: Literal["1.0.0"]
    action_id: UUID
    farmer_id: UUID
    farmland_id: UUID
    season_id: UUID | None = None
    source_module: Literal["m2", "m3", "m4", "m5", "m6"]
    status: Literal[
        "draft", "awaiting_confirmation", "confirmed", "applied", "rejected", "expired", "conflict", "failed"
    ]
    version: int = Field(ge=1)
    created_at: AwareDatetime
    expires_at: AwareDatetime
    preconditions: list[ActionPrecondition] = Field(min_length=1, max_length=100)
    task_diff: TaskDiff
    required_consent_purposes: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "ProposedAction":
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        if len(self.required_consent_purposes) != len(set(self.required_consent_purposes)):
            raise ValueError("required consent purposes must be unique")
        return self


class ActionExecutionReceipt(ContractModel):
    contract_version: Literal["1.0.0"]
    receipt_id: UUID
    action_id: UUID
    farmer_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=200)
    action_version: int = Field(ge=1)
    status: Literal["applied", "rejected", "conflict", "failed"]
    created_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    result: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_receipt_times(self) -> "ActionExecutionReceipt":
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at must not precede created_at")
        return self


class ConsentRecordInput(ContractModel):
    contract_version: Literal["1.0.0"]
    purpose: Literal[
        "personalized_advice", "offline_storage", "speech_audio_transcription",
        "disease_problem_sync", "research",
    ]
    decision: Literal["granted", "denied", "withdrawn"]
    policy_version: str = Field(min_length=1, max_length=80)
    channel: Literal["explicit_tap", "voice_confirmed", "settings", "system_import"]
    captured_at: AwareDatetime


class ObservedSymptom(ContractModel):
    code: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    source: Literal["farmer_reported", "model_suggested", "expert_verified"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    observed_at: AwareDatetime | None = None


class DiseaseProblemSyncRequest(ContractModel):
    contract_version: Literal["1.0.0"]
    disease_result_id: UUID
    farmland_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=200)
    mode: Literal["legacy", "deferred_confirmation"]
    assessment: Literal["possible_issue", "healthy", "uncertain"]
    possible_issue: str | None = Field(default=None, max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)
    farmer_confirmation: Literal[
        "not_required", "not_supported", "pending", "confirmed", "denied"
    ]
    consent_receipt_id: UUID | None = None
    symptoms: list[ObservedSymptom] | None = Field(default=None, max_length=100)
    requested_at: AwareDatetime

    @model_validator(mode="after")
    def enforce_deferred_consent(self) -> "DiseaseProblemSyncRequest":
        if self.assessment == "possible_issue" and not self.possible_issue:
            raise ValueError("possible-issue assessments require the saved result label")
        if self.assessment != "possible_issue" and self.possible_issue is not None:
            raise ValueError("healthy or uncertain assessments cannot create a problem candidate")
        if self.assessment != "possible_issue" and self.farmer_confirmation != "not_required":
            raise ValueError("healthy or uncertain assessments do not require problem confirmation")
        if (
            self.mode == "deferred_confirmation"
            and self.assessment == "possible_issue"
            and self.farmer_confirmation not in {"pending", "confirmed", "denied"}
        ):
            raise ValueError("deferred sync requires an explicit pending, confirmed, or denied state")
        if self.farmer_confirmation == "confirmed" and self.consent_receipt_id is None:
            raise ValueError("confirmed disease sync requires a consent receipt")
        if self.farmer_confirmation == "confirmed" and self.assessment != "possible_issue":
            raise ValueError("only a possible issue can be confirmed for farm-problem sync")
        return self


class DiseaseProblemSyncReceipt(ContractModel):
    contract_version: Literal["1.0.0"]
    disease_result_id: UUID
    farmland_id: UUID
    status: Literal[
        "awaiting_confirmation", "synchronized", "no_problem", "ineligible", "conflict", "unavailable"
    ]
    problem_id: UUID | None = None
    retriable: bool
    created_at: AwareDatetime

    @model_validator(mode="after")
    def validate_sync_outcome(self) -> "DiseaseProblemSyncReceipt":
        if self.status == "synchronized" and self.problem_id is None:
            raise ValueError("synchronized results must identify the existing or newly created problem")
        if self.status != "synchronized" and self.problem_id is not None:
            raise ValueError("only a synchronized result may link a farm problem")
        return self


class ApiError(ContractModel):
    contract_version: Literal["1.0.0"]
    code: Literal[
        "unavailable", "invalid_input", "not_found", "forbidden", "conflict", "expired", "stale_evidence"
    ]
    message: str = Field(min_length=1, max_length=500)
    retriable: bool
    trace_id: str | None = Field(default=None, max_length=100)
    details: dict[str, Any] = Field(default_factory=dict)


ContractCatalog.model_rebuild()
