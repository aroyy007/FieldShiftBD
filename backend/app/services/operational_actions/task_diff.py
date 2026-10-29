from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.challenge.v1 import ProposedAction, TaskDiff, TaskDiffApplyResult
from app.models import Farmland, Season, Task


class OwnerOperationConflict(Exception):
    """A farm-state precondition changed before the requested diff was applied."""


class TaskDiffOwnerOperation:
    """Apply a validated task diff using the caller's open SQLAlchemy transaction.

    This owner operation intentionally never commits. The action coordinator's
    unit of work owns the transaction boundary and receipt/outbox writes.
    """

    def apply(
        self,
        session: Session,
        action: ProposedAction,
        task_diff: TaskDiff,
        *,
        now: datetime | None = None,
    ) -> TaskDiffApplyResult:
        now = now or datetime.now(timezone.utc)
        farmland = session.scalar(
            select(Farmland.id).where(
                Farmland.id == action.farmland_id,
                Farmland.farmer_id == action.farmer_id,
            )
        )
        if farmland is None:
            raise OwnerOperationConflict("farmland ownership changed")
        if action.season_id is None:
            raise OwnerOperationConflict("task updates require a season")
        season_exists = session.scalar(
            select(Season.id).where(
                Season.id == action.season_id,
                Season.farmland_id == action.farmland_id,
                Season.status.in_(("planned", "active")),
            )
        )
        if season_exists is None:
            raise OwnerOperationConflict("the target season is no longer writable")

        created: list[UUID] = []
        updated: list[UUID] = []
        completed: list[UUID] = []
        cancelled: list[UUID] = []
        task_source = {
            "m2": "season_plan",
            "m3": "system",
            "m4": "weather",
            "m5": "farmer",
            "m6": "disease",
        }[action.source_module]

        for change in task_diff.operations:
            source_reference = _stable_source_reference(action.action_id, change.reference)
            if change.operation == "create":
                task = session.scalar(
                    select(Task).where(
                        Task.season_id == action.season_id,
                        Task.source_reference == source_reference,
                    )
                )
                if task is not None:
                    if not _create_matches(task, change, task_source):
                        raise OwnerOperationConflict("task reference already belongs to a different change")
                    created.append(task.id)
                    continue
                task = Task(
                    farmland_id=action.farmland_id,
                    season_id=action.season_id,
                    title=change.title or "",
                    description=change.description,
                    due_at=change.due_at,
                    status="pending",
                    priority=change.priority or "normal",
                    source=task_source,
                    source_reference=source_reference,
                )
                session.add(task)
                session.flush()
                created.append(task.id)
                continue

            task = session.scalar(
                select(Task)
                .where(
                    Task.id == change.task_id,
                    Task.farmland_id == action.farmland_id,
                    Task.season_id == action.season_id,
                )
                .with_for_update()
            )
            if task is None:
                raise OwnerOperationConflict("task no longer belongs to this farm and season")
            if task.status != change.expected_status:
                raise OwnerOperationConflict("task status changed after the proposal was made")
            if task.status != "pending":
                raise OwnerOperationConflict("completed or closed tasks cannot be rewritten")

            if change.operation == "update":
                if change.title is not None:
                    task.title = change.title
                if change.description is not None:
                    task.description = change.description
                if change.due_at is not None:
                    task.due_at = change.due_at
                if change.priority is not None:
                    task.priority = change.priority
                task.updated_at = now
                updated.append(task.id)
            elif change.operation == "complete":
                task.status = "completed"
                task.completed_at = now
                task.updated_at = now
                completed.append(task.id)
            elif change.operation == "cancel":
                task.status = "cancelled"
                task.updated_at = now
                cancelled.append(task.id)

        session.flush()
        return TaskDiffApplyResult(
            contract_version="1.0.0",
            action_id=action.action_id,
            farmer_id=action.farmer_id,
            farmland_id=action.farmland_id,
            season_id=action.season_id,
            created_task_ids=created,
            updated_task_ids=updated,
            completed_task_ids=completed,
            cancelled_task_ids=cancelled,
        )


def _stable_source_reference(action_id: UUID, reference: str) -> str:
    digest = hashlib.sha256(f"{action_id}:{reference}".encode("utf-8")).hexdigest()
    return f"action:{digest}"


def _create_matches(task: Task, change: Any, task_source: str) -> bool:
    return (
        task.title == change.title
        and task.description == change.description
        and task.due_at == change.due_at
        and task.priority == (change.priority or "normal")
        and task.source == task_source
        and task.status == "pending"
    )
