from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.farm_state import ProblemRead


DiseaseOutcome = Literal["healthy", "uncertain", "possible_disease"]
ConfidenceLevel = Literal["low", "moderate", "high"]
ProblemSyncStatus = Literal["not_required", "created", "reused", "failed"]
VerificationStatus = Literal[
    "not_configured",
    "verified_healthy",
    "verified_issue",
    "gemini_only_issue",
    "disagreement",
    "uncertain",
    "unavailable",
]
GeminiFinding = Literal["healthy", "possible_issue", "uncertain", "not_crop"]
GeminiCropMatch = Literal[
    "matches_current_crop",
    "different_crop",
    "uncertain",
]


class DiseaseVerificationRead(BaseModel):
    status: VerificationStatus
    finding: GeminiFinding | None = None
    crop_match: GeminiCropMatch | None = None
    visible_signs: str | None = None
    model: str | None = None


class DiseaseResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    season_id: UUID | None
    crop_id: UUID | None
    crop_name: str | None = None
    possible_issue: str | None
    confidence: float | None
    symptoms: list[str]
    recommended_actions: list[str]
    model_details: dict[str, Any]
    created_at: datetime


class DiseaseAnalysisResponse(BaseModel):
    disease_result: DiseaseResultRead
    outcome: DiseaseOutcome
    verification: DiseaseVerificationRead
    confidence_level: ConfidenceLevel
    crop_name: str
    growth_stage_name: str | None
    farm_problem: ProblemRead | None
    problem_sync: ProblemSyncStatus
    message: str
    disclaimer: str


class DiseaseProblemSyncResponse(BaseModel):
    disease_result: DiseaseResultRead
    farm_problem: ProblemRead | None
    problem_sync: ProblemSyncStatus
    message: str
