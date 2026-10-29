"""Protocols used at module boundaries; adapters own transport and storage."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.contracts.challenge.v1 import (
    AdaptiveRecommendation,
    ActionExecutionReceipt,
    DistrictClimateBundle,
    DiseaseProblemSyncReceipt,
    DiseaseProblemSyncRequest,
    FarmProfileSnapshot,
    PlantingWindowAdvisory,
    ProposedAction,
    RotationComparison,
    TaskDiff,
    TaskDiffApplyResult,
)


class AdapterUnavailable(RuntimeError):
    """A required adapter is intentionally disabled or not yet installed."""


class ArtifactNotFound(RuntimeError):
    """The requested district/version is absent from the local cache."""


class StaleArtifact(RuntimeError):
    """A cache manifest or source artifact has passed its allowed freshness."""


class AdapterConflict(RuntimeError):
    """A version or precondition changed while an operation was pending."""


class FarmProfileSnapshotReader(Protocol):
    def get_snapshot(self, farmer_id: UUID, farmland_id: UUID) -> FarmProfileSnapshot: ...


class DistrictClimateBundleProvider(Protocol):
    def get_bundle(self, district_code: str, *, as_of: datetime) -> DistrictClimateBundle: ...


class PlantingWindowAdvisor(Protocol):
    def advise(
        self, snapshot: FarmProfileSnapshot, bundle: DistrictClimateBundle, crop_code: str
    ) -> PlantingWindowAdvisory: ...


class RotationComparisonProvider(Protocol):
    def compare(self, snapshot: FarmProfileSnapshot) -> RotationComparison: ...


class AdaptiveDecisionProvider(Protocol):
    def evaluate(self, snapshot: FarmProfileSnapshot, question: str) -> AdaptiveRecommendation: ...


class ActionConfirmationProvider(Protocol):
    def propose(self, proposal: ProposedAction) -> ProposedAction: ...

    def confirm(
        self,
        farmer_id: UUID,
        action_id: UUID,
        expected_version: int,
        idempotency_key: str,
        *,
        decision: str = "confirm",
    ) -> ActionExecutionReceipt: ...


class TaskDiffOwner(Protocol):
    """M3 applies the diff on the caller's transaction and never commits."""

    def apply(
        self,
        session: object,
        action: ProposedAction,
        task_diff: TaskDiff,
        *,
        now: datetime | None = None,
    ) -> TaskDiffApplyResult: ...


class DiseaseProblemSyncProvider(Protocol):
    def request_sync(self, request: DiseaseProblemSyncRequest) -> DiseaseProblemSyncReceipt: ...
