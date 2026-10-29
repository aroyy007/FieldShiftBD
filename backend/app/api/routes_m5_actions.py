"""Farm-scoped M5 action proposals, explicit confirmation, and consent records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.challenge.v1 import (
    ActionExecutionReceipt,
    ConsentRecordInput,
    ProposedAction,
)
from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models import Farmland, ProposedAction as ProposedActionRow
from app.services.actions.coordinator import ActionConflict
from app.services.m5_actions import normalize_pending_task_status

router = APIRouter(prefix="/farmlands", tags=["Conversational Layer — Module 5 Actions"])
consent_router = APIRouter(prefix="/challenge", tags=["Challenge consent"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentFarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


class ActionConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    decision: Literal["confirm", "reject"] = "confirm"


class ConsentRecordResponse(BaseModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    consent_record_id: UUID


def _require_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> Farmland:
    farmland = db.scalar(
        select(Farmland).where(Farmland.id == farmland_id, Farmland.farmer_id == farmer_id)
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found")
    return farmland


def _as_utc(value: datetime) -> datetime:
    """Restore SQLite's dropped timezone when serializing persisted timestamps."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _coordinator(request: Request):
    runtime = request.app.state.challenge_runtime
    return runtime.require_adapter("action_confirmation")


@router.get("/{farmland_id}/actions/pending", response_model=list[ProposedAction])
def list_pending_actions(
    farmland_id: UUID,
    request: Request,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    _coordinator(request)
    _require_farmland(db, farmland_id, farmer_id)
    rows = db.scalars(
        select(ProposedActionRow)
        .where(
            ProposedActionRow.farmland_id == farmland_id,
            ProposedActionRow.farmer_id == farmer_id,
            ProposedActionRow.status == "awaiting_confirmation",
            ProposedActionRow.expires_at > datetime.now(timezone.utc),
        )
        .order_by(ProposedActionRow.created_at.desc())
        .limit(20)
    ).all()
    return [
        ProposedAction.model_validate(
            {
                "contract_version": row.contract_version,
                "action_id": row.id,
                "farmer_id": row.farmer_id,
                "farmland_id": row.farmland_id,
                "season_id": row.season_id,
                "source_module": row.source_module,
                "status": row.status,
                "version": row.version,
                "created_at": _as_utc(row.created_at),
                "expires_at": _as_utc(row.expires_at),
                "preconditions": row.preconditions,
                "task_diff": row.task_diff,
                "required_consent_purposes": row.required_consent_purposes,
            }
        )
        for row in rows
    ]


@router.post(
    "/{farmland_id}/actions/proposals",
    response_model=ProposedAction,
    status_code=status.HTTP_201_CREATED,
)
def create_action_proposal(
    farmland_id: UUID,
    payload: ProposedAction,
    request: Request,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    coordinator = _coordinator(request)
    _require_farmland(db, farmland_id, farmer_id)
    if payload.farmland_id != farmland_id or payload.farmer_id != farmer_id:
        raise HTTPException(status_code=409, detail="Action scope does not match the signed-in farmer and farm")
    # This bearer-authenticated app route has farmer identity, not a trusted
    # M2/M3/M4/M6 service identity; module producers use the coordinator from
    # their server-side adapter rather than claiming another module here.
    if payload.source_module != "m5":
        raise HTTPException(status_code=422, detail="This authenticated proposal route only accepts M5 actions")
    try:
        return coordinator.propose(normalize_pending_task_status(payload))
    except ActionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/{farmland_id}/actions/{action_id}/confirm",
    response_model=ActionExecutionReceipt,
)
def confirm_action(
    farmland_id: UUID,
    action_id: UUID,
    payload: ActionConfirmationRequest,
    request: Request,
    farmer_id: CurrentFarmerId,
    db: DbSession,
):
    coordinator = _coordinator(request)
    _require_farmland(db, farmland_id, farmer_id)
    owned_action = db.scalar(
        select(ProposedActionRow.id).where(
            ProposedActionRow.id == action_id,
            ProposedActionRow.farmland_id == farmland_id,
            ProposedActionRow.farmer_id == farmer_id,
        )
    )
    if owned_action is None:
        raise HTTPException(status_code=404, detail="Action not found for this farm")
    try:
        return coordinator.confirm(
            farmer_id,
            action_id,
            payload.expected_version,
            payload.idempotency_key,
            decision=payload.decision,
        )
    except ActionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@consent_router.post("/consents", response_model=ConsentRecordResponse)
def record_consent(
    payload: ConsentRecordInput,
    request: Request,
    farmer_id: CurrentFarmerId,
):
    adapters = request.app.state.challenge_runtime.adapters
    coordinator = adapters.get("consent_records") or adapters.get("action_confirmation")
    if coordinator is None:
        from app.services.foundation.runtime import ChallengeUnavailable

        raise ChallengeUnavailable("consent storage")
    idempotency_key = request.headers.get("Idempotency-Key", "")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    try:
        consent_id = coordinator.record_consent(farmer_id, payload, idempotency_key)
    except ActionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ConsentRecordResponse(consent_record_id=consent_id)
