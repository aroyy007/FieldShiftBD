from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.contracts.challenge.v1 import ConsentRecordInput, ProposedAction
from app.models import (
    ActionReceipt,
    ConsentRecord,
    Crop,
    DeliveryOutbox,
    Farmland,
    Farmer,
    ProposedAction as ProposedActionRow,
    Season,
    Task,
)
from app.services.actions.coordinator import (
    ActionCoordinator,
    ActionIdempotencyConflict,
    ConsentIdempotencyConflict,
)
from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
from app.services.operational_actions.task_diff import TaskDiffOwnerOperation

NOW = datetime(2026, 10, 29, 9, tzinfo=timezone.utc)


class FixedPreconditions:
    def __init__(self, conflicts=None):
        self._conflicts = conflicts or []

    def conflicts(self, session, action):
        return self._conflicts


def _farmer_farm_and_season(sessions):
    with sessions() as db:
        farmer = Farmer(name="Synthetic Farmer A", phone_e164="+8801700000100")
        crop = Crop(name="Synthetic Aman Rice")
        db.add_all([farmer, crop])
        db.flush()
        farmland = Farmland(
            farmer_id=farmer.id,
            name="Synthetic North Field",
            land_area_sqm=1000,
            land_area_display_unit="square_metre",
        )
        db.add(farmland)
        db.flush()
        season = Season(farmland_id=farmland.id, crop_id=crop.id, status="active")
        db.add(season)
        db.commit()
        return farmer.id, farmland.id, season.id


def _coordinator(sessions, preconditions=None, operation=None, outbox_writer=None):
    return ActionCoordinator(
        SQLAlchemyUnitOfWorkFactory(sessions),
        operation or TaskDiffOwnerOperation(),
        preconditions or FixedPreconditions(),
        clock=lambda: NOW,
        outbox_writer=outbox_writer,
    )


def _consent():
    return ConsentRecordInput.model_validate(
        {
            "contract_version": "1.0.0",
            "purpose": "personalized_advice",
            "decision": "granted",
            "policy_version": "2026-10-v1",
            "channel": "explicit_tap",
            "captured_at": NOW.isoformat(),
        }
    )


def _proposal(farmer_id, farmland_id, season_id, *, action_id=None):
    return ProposedAction.model_validate(
        {
            "contract_version": "1.0.0",
            "action_id": action_id or str(uuid4()),
            "farmer_id": farmer_id,
            "farmland_id": farmland_id,
            "season_id": season_id,
            "source_module": "m2",
            "status": "awaiting_confirmation",
            "version": 1,
            "created_at": NOW.isoformat(),
            "expires_at": "2026-10-30T09:00:00Z",
            "preconditions": [
                {
                    "kind": "farm_state_matches",
                    "subject": "season.crop_code",
                    "expected_value": "synthetic_aman",
                    "observed_at": NOW.isoformat(),
                }
            ],
            "task_diff": {
                "operations": [
                    {
                        "operation": "create",
                        "reference": "aman-drainage-check",
                        "title": "Check field drainage",
                        "priority": "high",
                    }
                ]
            },
            "required_consent_purposes": ["personalized_advice"],
        }
    )


def test_confirmation_applies_owner_operation_once_and_replays_receipt(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions)
    coordinator.record_consent(farmer_id, _consent(), "consent-synthetic-01")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    first = coordinator.confirm(
        farmer_id, proposal.action_id, 1, "confirm-synthetic-01", decision="confirm"
    )
    replay = coordinator.confirm(
        farmer_id, proposal.action_id, 1, "confirm-synthetic-01", decision="confirm"
    )

    assert first.status == "applied"
    assert replay.receipt_id == first.receipt_id
    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 1
        assert db.scalar(select(func.count()).select_from(ActionReceipt)) == 1
        assert db.scalar(select(func.count()).select_from(DeliveryOutbox)) == 1
        action = db.get(ProposedActionRow, proposal.action_id)
        assert action.status == "applied" and action.version == 2


def test_confirmation_fails_closed_without_consent_and_does_not_write_tasks(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions)
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    receipt = coordinator.confirm(
        farmer_id, proposal.action_id, 1, "confirm-needs-consent", decision="confirm"
    )

    assert receipt.status == "conflict"
    assert receipt.result == {"code": "consent_required", "purposes": ["personalized_advice"]}
    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
        assert db.get(ProposedActionRow, proposal.action_id).status == "awaiting_confirmation"


def test_stale_precondition_conflicts_without_partial_domain_mutation(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions, FixedPreconditions(["season crop changed"]))
    coordinator.record_consent(farmer_id, _consent(), "consent-synthetic-02")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    receipt = coordinator.confirm(
        farmer_id, proposal.action_id, 1, "confirm-stale-state", decision="confirm"
    )

    assert receipt.status == "conflict"
    assert receipt.result["code"] == "precondition_changed"
    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
        assert db.scalar(select(func.count()).select_from(DeliveryOutbox)) == 0
        assert db.get(ProposedActionRow, proposal.action_id).status == "conflict"


def test_reusing_idempotency_key_for_different_action_is_rejected(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions)
    coordinator.record_consent(farmer_id, _consent(), "consent-synthetic-03")
    first_action = _proposal(farmer_id, farmland_id, season_id)
    second_action = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(first_action)
    coordinator.propose(second_action)
    coordinator.confirm(farmer_id, first_action.action_id, 1, "same-confirm-key", decision="confirm")

    with pytest.raises(ActionIdempotencyConflict):
        coordinator.confirm(farmer_id, second_action.action_id, 1, "same-confirm-key", decision="confirm")


def test_reusing_consent_key_for_changed_decision_is_rejected(foundation_sessions):
    farmer_id, _, _ = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions)
    coordinator.record_consent(farmer_id, _consent(), "same-consent-key")
    changed = _consent().model_copy(update={"decision": "withdrawn"})

    with pytest.raises(ConsentIdempotencyConflict):
        coordinator.record_consent(farmer_id, changed, "same-consent-key")

    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(ConsentRecord)) == 1


def test_latest_consent_uses_server_record_order_not_client_clock(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)
    coordinator = _coordinator(foundation_sessions)
    coordinator.record_consent(farmer_id, _consent(), "consent-time-grant")
    backdated_denial = _consent().model_copy(update={
        "decision": "denied",
        "captured_at": NOW - timedelta(days=1),
    })
    coordinator.record_consent(farmer_id, backdated_denial, "consent-time-denial")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    receipt = coordinator.confirm(farmer_id, proposal.action_id, 1, "confirm-after-denial")

    assert receipt.status == "conflict"
    assert receipt.result["code"] == "consent_required"


def test_transaction_rolls_back_task_receipt_action_and_outbox_on_owner_failure(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)

    class FailAfterApplyingTask:
        def apply(self, session, action, task_diff, *, now=None):
            TaskDiffOwnerOperation().apply(session, action, task_diff, now=now)
            raise RuntimeError("synthetic failure after owner write")

    coordinator = _coordinator(foundation_sessions, operation=FailAfterApplyingTask())
    coordinator.record_consent(farmer_id, _consent(), "consent-synthetic-04")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    with pytest.raises(RuntimeError, match="synthetic failure"):
        coordinator.confirm(
            farmer_id, proposal.action_id, 1, "confirm-rollback-key", decision="confirm"
        )

    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
        assert db.scalar(select(func.count()).select_from(ActionReceipt)) == 0
        assert db.scalar(select(func.count()).select_from(DeliveryOutbox)) == 0
        action = db.get(ProposedActionRow, proposal.action_id)
        assert action.status == "awaiting_confirmation" and action.version == 1


def test_transaction_rolls_back_when_outbox_enqueue_fails_after_domain_write(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)

    class FailingOutbox:
        def enqueue(self, *_args, **_kwargs):
            raise RuntimeError("synthetic outbox failure")

    coordinator = _coordinator(foundation_sessions, outbox_writer=FailingOutbox())
    coordinator.record_consent(farmer_id, _consent(), "consent-outbox-rollback")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    with pytest.raises(RuntimeError, match="outbox failure"):
        coordinator.confirm(farmer_id, proposal.action_id, 1, "confirm-outbox-rollback")

    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
        assert db.scalar(select(func.count()).select_from(ActionReceipt)) == 0
        assert db.scalar(select(func.count()).select_from(DeliveryOutbox)) == 0
        action = db.get(ProposedActionRow, proposal.action_id)
        assert action.status == "awaiting_confirmation" and action.version == 1


def test_m3_owner_result_must_match_action_farm_scope(foundation_sessions):
    farmer_id, farmland_id, season_id = _farmer_farm_and_season(foundation_sessions)

    class WrongFarmResult:
        def apply(self, session, action, task_diff, *, now=None):
            result = TaskDiffOwnerOperation().apply(session, action, task_diff, now=now)
            return result.model_copy(update={"farmland_id": uuid4()})

    coordinator = _coordinator(foundation_sessions, operation=WrongFarmResult())
    coordinator.record_consent(farmer_id, _consent(), "consent-scope-check")
    proposal = _proposal(farmer_id, farmland_id, season_id)
    coordinator.propose(proposal)

    receipt = coordinator.confirm(farmer_id, proposal.action_id, 1, "confirm-scope-check")

    assert receipt.status == "conflict"
    assert receipt.result["code"] == "farm_state_changed"
    with foundation_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
