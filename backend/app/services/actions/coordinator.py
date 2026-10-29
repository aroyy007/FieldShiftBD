from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.contracts.challenge.v1 import (
    ActionExecutionReceipt,
    ConsentRecordInput,
    CONTRACT_VERSION,
    ProposedAction,
    TaskDiff,
    TaskDiffApplyResult,
)
from app.core.time_utils import to_utc
from app.models import (
    ActionReceipt,
    ConsentRecord,
    Farmland,
    Farmer,
    ProposedAction as ProposedActionRow,
)
from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
from app.services.actions.outbox import TransactionalOutboxWriter
from app.services.operational_actions.task_diff import OwnerOperationConflict


class PreconditionEvaluator(Protocol):
    def conflicts(
        self, session: Session, action: ProposedAction
    ) -> list[str]: ...


class TaskDiffOperation(Protocol):
    def apply(
        self,
        session: Session,
        action: ProposedAction,
        task_diff: Any,
        *,
        now: datetime | None = None,
    ) -> TaskDiffApplyResult: ...


class ActionConflict(Exception):
    """The client must refresh or create a new proposal before retrying."""


class ActionIdempotencyConflict(ActionConflict):
    """An idempotency key was reused for a different request."""


class ConsentIdempotencyConflict(ActionConflict):
    """A consent idempotency key was reused for a different decision."""


class ActionCoordinator:
    """Persist and apply user-confirmed task changes as one database commit."""

    def __init__(
        self,
        uow_factory: SQLAlchemyUnitOfWorkFactory,
        task_diff_operation: TaskDiffOperation,
        precondition_evaluator: PreconditionEvaluator,
        *,
        clock=None,
        outbox_writer=None,
    ) -> None:
        self._uow_factory = uow_factory
        self._task_diff_operation = task_diff_operation
        self._precondition_evaluator = precondition_evaluator
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._outbox_writer = outbox_writer or TransactionalOutboxWriter()

    def record_consent(self, farmer_id: UUID, consent: ConsentRecordInput, idempotency_key: str) -> UUID:
        if len(idempotency_key) < 8 or len(idempotency_key) > 200:
            raise ValueError("consent idempotency key must be between 8 and 200 characters")
        now = self._now()
        if to_utc(consent.captured_at) > now + timedelta(minutes=5):
            raise ValueError("consent capture time cannot be in the future")
        fingerprint = _fingerprint(
            {**consent.model_dump(mode="json"), "farmer_id": str(farmer_id)}
        )
        with self._uow_factory() as uow:
            assert uow.session is not None
            db = uow.session
            if db.get(Farmer, farmer_id) is None:
                raise ActionConflict("farmer does not exist")
            # Serialize decisions for one consent purpose so its server-side
            # version remains monotonic even when clients submit concurrently.
            _lock_idempotency_key(
                db, farmer_id, consent.purpose, namespace="consent-order"
            )
            _lock_idempotency_key(db, farmer_id, idempotency_key, namespace="consent")
            existing = db.scalar(
                select(ConsentRecord).where(
                    ConsentRecord.farmer_id == farmer_id,
                    ConsentRecord.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ConsentIdempotencyConflict("consent request key was reused")
                return existing.id
            version = (
                db.scalar(
                    select(func.max(ConsentRecord.version)).where(
                        ConsentRecord.farmer_id == farmer_id,
                        ConsentRecord.purpose == consent.purpose,
                    )
                )
                or 0
            ) + 1
            record = ConsentRecord(
                farmer_id=farmer_id,
                purpose=consent.purpose,
                version=version,
                decision=consent.decision,
                policy_version=consent.policy_version,
                channel=consent.channel,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                captured_at=consent.captured_at,
            )
            db.add(record)
            db.flush()
            return record.id

    def propose(self, proposal: ProposedAction) -> ProposedAction:
        now = self._now()
        if proposal.status != "awaiting_confirmation":
            raise ValueError("only awaiting_confirmation proposals can be submitted")
        if proposal.created_at > now or proposal.expires_at <= now:
            raise ValueError("proposal must be active at submission time")
        with self._uow_factory() as uow:
            assert uow.session is not None
            db = uow.session
            farmer = db.get(Farmer, proposal.farmer_id)
            farmland = db.scalar(
                select(Farmland).where(
                    Farmland.id == proposal.farmland_id,
                    Farmland.farmer_id == proposal.farmer_id,
                )
            )
            if farmer is None or farmland is None:
                raise ActionConflict("proposal owner or farmland could not be verified")
            row = ProposedActionRow(
                id=proposal.action_id,
                farmer_id=proposal.farmer_id,
                farmland_id=proposal.farmland_id,
                season_id=proposal.season_id,
                source_module=proposal.source_module,
                status="awaiting_confirmation",
                version=proposal.version,
                contract_version=proposal.contract_version,
                preconditions=[item.model_dump(mode="json") for item in proposal.preconditions],
                task_diff=proposal.task_diff.model_dump(mode="json"),
                required_consent_purposes=proposal.required_consent_purposes,
                created_at=proposal.created_at,
                updated_at=now,
                expires_at=proposal.expires_at,
            )
            db.add(row)
            db.flush()
        return proposal

    def confirm(
        self,
        farmer_id: UUID,
        action_id: UUID,
        expected_version: int,
        idempotency_key: str,
        *,
        decision: str = "confirm",
    ) -> ActionExecutionReceipt:
        if decision not in {"confirm", "reject"}:
            raise ValueError("decision must be confirm or reject")
        if len(idempotency_key) < 8 or len(idempotency_key) > 200:
            raise ValueError("idempotency key must be between 8 and 200 characters")
        now = self._now()
        request_fingerprint = _fingerprint(
            {
                "farmer_id": str(farmer_id),
                "action_id": str(action_id),
                "expected_version": expected_version,
                "decision": decision,
            }
        )
        with self._uow_factory() as uow:
            assert uow.session is not None
            db = uow.session
            _lock_idempotency_key(db, farmer_id, idempotency_key)
            previous = db.scalar(
                select(ActionReceipt).where(
                    ActionReceipt.farmer_id == farmer_id,
                    ActionReceipt.idempotency_key == idempotency_key,
                )
            )
            if previous is not None:
                if previous.request_fingerprint != request_fingerprint:
                    raise ActionIdempotencyConflict("action request key was reused")
                return _as_receipt(previous)

            action_row = db.scalar(
                select(ProposedActionRow)
                .where(
                    ProposedActionRow.id == action_id,
                    ProposedActionRow.farmer_id == farmer_id,
                )
                .with_for_update()
            )
            if action_row is None:
                raise ActionConflict("action was not found for this farmer")
            if action_row.status != "awaiting_confirmation":
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "action_not_pending",
                )
            if action_row.version != expected_version:
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "version_changed",
                )
            if to_utc(action_row.expires_at) <= now:
                action_row.status = "expired"
                action_row.version += 1
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "action_expired",
                )
            proposal = _as_proposal(action_row)
            if decision == "reject":
                action_row.status = "rejected"
                action_row.version += 1
                return self._save_terminal_receipt(
                    db, action_row, farmer_id, idempotency_key, request_fingerprint,
                    expected_version, "rejected", {"code": "farmer_rejected"}, now,
                    event_type="action.rejected",
                )

            missing_consents = self._missing_consents(db, farmer_id, proposal.required_consent_purposes)
            if missing_consents:
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "consent_required",
                    details={"purposes": missing_consents},
                )
            precondition_conflicts = self._precondition_evaluator.conflicts(db, proposal)
            if precondition_conflicts:
                action_row.status = "conflict"
                action_row.version += 1
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "precondition_changed",
                    details={"conflicts": precondition_conflicts},
                )

            try:
                with db.begin_nested():
                    operation_result = self._task_diff_operation.apply(
                        db, proposal, proposal.task_diff, now=now
                    )
                    result = TaskDiffApplyResult.model_validate(operation_result)
                    if (
                        result.action_id != proposal.action_id
                        or result.farmer_id != proposal.farmer_id
                        or result.farmland_id != proposal.farmland_id
                        or result.season_id != proposal.season_id
                    ):
                        raise OwnerOperationConflict("M3 task receipt scope does not match the confirmed action")
            except OwnerOperationConflict as exc:
                action_row.status = "conflict"
                action_row.version += 1
                return self._save_conflict(
                    db, action_row, farmer_id, idempotency_key,
                    request_fingerprint, expected_version, now, "farm_state_changed",
                    details={"reason": str(exc)},
                )

            action_row.status = "applied"
            action_row.version += 1
            return self._save_terminal_receipt(
                db, action_row, farmer_id, idempotency_key, request_fingerprint,
                expected_version, "applied", result.model_dump(mode="json"), now, event_type="action.applied",
            )

    def _missing_consents(self, db: Session, farmer_id: UUID, purposes: list[str]) -> list[str]:
        missing = []
        for purpose in purposes:
            latest = db.scalar(
                select(ConsentRecord)
                .where(ConsentRecord.farmer_id == farmer_id, ConsentRecord.purpose == purpose)
                .order_by(ConsentRecord.version.desc())
                .limit(1)
            )
            if latest is None or latest.decision != "granted":
                missing.append(purpose)
        return missing

    def _save_conflict(
        self, db, action_row, farmer_id, key, request_fingerprint,
        expected_version, now, code, details=None,
    ):
        return self._save_terminal_receipt(
            db, action_row, farmer_id, key, request_fingerprint, expected_version,
            "conflict", {"code": code, **(details or {})}, now, event_type=None,
        )

    def _save_terminal_receipt(
        self, db, action_row, farmer_id, key, request_fingerprint,
        action_version, status, result, now, *, event_type,
    ):
        receipt = ActionReceipt(
            action_id=action_row.id,
            farmer_id=farmer_id,
            idempotency_key=key,
            request_fingerprint=request_fingerprint,
            action_version=action_version,
            status=status,
            result=result,
            created_at=now,
            completed_at=now,
        )
        db.add(receipt)
        db.flush()
        if event_type is not None:
            self._outbox_writer.enqueue(
                db,
                receipt_id=receipt.id,
                event_type=event_type,
                idempotency_key=f"action-receipt:{receipt.id}:{event_type}",
                payload={
                    "contract_version": CONTRACT_VERSION,
                    "receipt_id": str(receipt.id),
                    "action_id": str(action_row.id),
                    "farmer_id": str(farmer_id),
                    "status": status,
                },
                available_at=now,
            )
        db.flush()
        return _as_receipt(receipt)

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware UTC datetime")
        return now.astimezone(timezone.utc)


def _fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lock_idempotency_key(db: Session, farmer_id: UUID, key: str, *, namespace: str = "action") -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        # Serialize retries with a per-farmer, per-key transaction-scoped lock.
        lock_key = f"fieldshift-{namespace}:{farmer_id}:{key}"
        db.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(lock_key, 0))))


def _as_proposal(row: ProposedActionRow) -> ProposedAction:
    return ProposedAction.model_validate(
        {
            "contract_version": row.contract_version,
            "action_id": row.id,
            "farmer_id": row.farmer_id,
            "farmland_id": row.farmland_id,
            "season_id": row.season_id,
            "source_module": row.source_module,
            "status": row.status,
            "version": row.version,
            "created_at": to_utc(row.created_at),
            "expires_at": to_utc(row.expires_at),
            "preconditions": row.preconditions,
            "task_diff": row.task_diff,
            "required_consent_purposes": row.required_consent_purposes,
        }
    )

def _as_receipt(row: ActionReceipt) -> ActionExecutionReceipt:
    return ActionExecutionReceipt.model_validate(
        {
            "contract_version": CONTRACT_VERSION,
            "receipt_id": row.id,
            "action_id": row.action_id,
            "farmer_id": row.farmer_id,
            "idempotency_key": row.idempotency_key,
            "action_version": row.action_version,
            "status": row.status,
            "created_at": to_utc(row.created_at),
            "completed_at": to_utc(row.completed_at) if row.completed_at else None,
            "result": row.result,
        }
    )
