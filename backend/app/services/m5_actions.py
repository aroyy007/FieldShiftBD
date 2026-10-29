"""M5 composition of confirmed actions over the existing M3 task operation."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.challenge.v1 import ProposedAction
from app.core.database import SessionLocal
from app.models import ConsentRecord, Farmland, Season, Task
from app.services.actions.coordinator import ActionCoordinator
from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
from app.services.operational_actions.task_diff import TaskDiffOwnerOperation


class FarmActionPreconditionEvaluator:
    """Fail closed when a proposal's captured farm/task/evidence state changed."""

    _FARMLAND_FIELDS = {
        "name",
        "soil_type",
        "land_type",
        "irrigation_available",
        "water_source",
        "budget_amount",
        "budget_currency",
        "previous_crop",
        "land_area_sqm",
    }
    _SEASON_FIELDS = {"id", "crop_id", "current_growth_stage_id", "status", "planting_date"}
    _TASK_SNAPSHOT_FIELDS = {"status", "title", "description", "due_at", "priority", "updated_at"}

    def conflicts(self, session: Session, action: ProposedAction) -> list[str]:
        conflicts: list[str] = []
        farmland = session.scalar(
            select(Farmland).where(
                Farmland.id == action.farmland_id,
                Farmland.farmer_id == action.farmer_id,
            )
        )
        season = session.scalar(
            select(Season).where(
                Season.id == action.season_id,
                Season.farmland_id == action.farmland_id,
            )
        ) if action.season_id else None
        task_snapshot_preconditions: set[UUID] = set()

        for index, precondition in enumerate(action.preconditions):
            label = f"preconditions[{index}]"
            if precondition.kind == "evidence_is_fresh":
                observed_at = precondition.observed_at
                if observed_at is None or precondition.max_age_seconds is None:
                    conflicts.append(f"{label}: evidence freshness requirements are incomplete")
                    continue
                age_seconds = (datetime.now(timezone.utc) - observed_at.astimezone(timezone.utc)).total_seconds()
                if age_seconds < 0 or age_seconds > precondition.max_age_seconds:
                    conflicts.append(f"{label}: evidence is stale or future-dated")
                continue

            if precondition.kind == "consent_is_active":
                purpose = precondition.subject
                latest = session.scalar(
                    select(ConsentRecord)
                    .where(
                        ConsentRecord.farmer_id == action.farmer_id,
                        ConsentRecord.purpose == purpose,
                    )
                    .order_by(ConsentRecord.version.desc())
                    .limit(1)
                )
                if latest is None or latest.decision != "granted":
                    conflicts.append(f"{label}: required consent is not active")
                continue

            if precondition.kind == "task_state_matches":
                try:
                    task_id = UUID(precondition.subject)
                except ValueError:
                    conflicts.append(f"{label}: task reference is invalid")
                    continue
                task_snapshot_preconditions.add(task_id)
                task = session.scalar(
                    select(Task)
                    .where(
                        Task.id == task_id,
                        Task.farmland_id == action.farmland_id,
                        Task.season_id == action.season_id,
                    )
                    .with_for_update()
                )
                change = next(
                    (item for item in action.task_diff.operations if item.task_id == task_id),
                    None,
                )
                expected = precondition.expected_value
                if task is None or change is None or not isinstance(expected, dict):
                    conflicts.append(f"{label}: a complete task snapshot is required")
                    continue
                if self._TASK_SNAPSHOT_FIELDS.difference(expected):
                    conflicts.append(f"{label}: a complete task snapshot is required")
                    continue
                if any(
                    not _same_value(getattr(task, field), expected[field])
                    for field in self._TASK_SNAPSHOT_FIELDS
                ):
                    conflicts.append(f"{label}: task snapshot changed")
                    continue
                continue

            actual = self._farm_state_value(precondition.subject, farmland, season)
            if actual is _UNKNOWN or not _same_value(actual, precondition.expected_value):
                conflicts.append(f"{label}: farm state changed or subject is unsupported")

        for change in action.task_diff.operations:
            if change.operation != "create" and change.task_id not in task_snapshot_preconditions:
                conflicts.append(f"task {change.task_id}: a complete task snapshot is required")
        return conflicts

    def _farm_state_value(self, subject: str, farmland: Farmland | None, season: Season | None) -> Any:
        parts = subject.split(".", maxsplit=1)
        if len(parts) != 2:
            return _UNKNOWN
        owner, field = parts
        if owner in {"farm", "farmland"} and field in self._FARMLAND_FIELDS:
            return getattr(farmland, field) if farmland is not None else _UNKNOWN
        if owner in {"season", "active_season"} and field in self._SEASON_FIELDS:
            return getattr(season, field) if season is not None else _UNKNOWN
        return _UNKNOWN


def normalize_pending_task_status(action: ProposedAction) -> ProposedAction:
    """Bind M5 task mutations to the pending status captured by their snapshot.

    The shared contract permits an omitted expected_status for complete/cancel.
    M5 fills it from its own full task snapshot so the M3 owner operation can
    keep its strict compare-and-set behavior unchanged.
    """

    snapshots = {
        precondition.subject: precondition.expected_value
        for precondition in action.preconditions
        if precondition.kind == "task_state_matches"
        and isinstance(precondition.expected_value, dict)
    }
    payload = action.model_dump(mode="python")
    changed = False
    for operation in payload["task_diff"]["operations"]:
        if operation["operation"] == "create" or operation["expected_status"] is not None:
            continue
        snapshot = snapshots.get(str(operation["task_id"]))
        if isinstance(snapshot, dict) and snapshot.get("status") == "pending":
            operation["expected_status"] = "pending"
            changed = True
    return ProposedAction.model_validate(payload) if changed else action


_UNKNOWN = object()


def _same_value(actual: Any, expected: Any) -> bool:
    if isinstance(actual, datetime) and isinstance(expected, str):
        try:
            expected_datetime = datetime.fromisoformat(expected.replace("Z", "+00:00"))
        except ValueError:
            return False
        actual_datetime = actual.replace(tzinfo=timezone.utc) if actual.tzinfo is None else actual.astimezone(timezone.utc)
        expected_datetime = (
            expected_datetime.replace(tzinfo=timezone.utc)
            if expected_datetime.tzinfo is None
            else expected_datetime.astimezone(timezone.utc)
        )
        return actual_datetime == expected_datetime
    if isinstance(actual, UUID):
        actual = str(actual)
    elif isinstance(actual, Decimal):
        actual = format(actual, "f")
    elif hasattr(actual, "isoformat"):
        actual = actual.isoformat()
    if isinstance(expected, (int, float)) and not isinstance(expected, bool) and isinstance(actual, str):
        try:
            return Decimal(actual) == Decimal(str(expected))
        except Exception:
            return False
    return actual == expected


def create_action_coordinator() -> ActionCoordinator:
    """Build the production coordinator without touching DB or network at import."""

    return ActionCoordinator(
        SQLAlchemyUnitOfWorkFactory(SessionLocal),
        TaskDiffOwnerOperation(),
        FarmActionPreconditionEvaluator(),
    )
