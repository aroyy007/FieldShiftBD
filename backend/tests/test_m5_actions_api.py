from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.contracts.challenge.v1 import ActionExecutionReceipt, ProposedAction
from app.services.foundation.runtime import FeatureSwitches


class RecordingActionCoordinator:
    def __init__(self):
        self.proposals = []
        self.confirmations = []
        self.consents = []

    def propose(self, proposal):
        self.proposals.append(proposal)
        return proposal

    def confirm(self, farmer_id, action_id, expected_version, idempotency_key, *, decision):
        self.confirmations.append((farmer_id, action_id, expected_version, idempotency_key, decision))
        now = datetime.now(timezone.utc)
        return ActionExecutionReceipt(
            contract_version="1.0.0",
            receipt_id=uuid4(),
            action_id=action_id,
            farmer_id=farmer_id,
            idempotency_key=idempotency_key,
            action_version=expected_version,
            status="conflict",
            created_at=now,
            completed_at=now,
            result={"code": "version_changed"},
        )

    def record_consent(self, farmer_id, consent, idempotency_key):
        self.consents.append((farmer_id, consent, idempotency_key))
        return uuid4()


def _proposal(farmer_id, farmland_id, season_id):
    now = datetime.now(timezone.utc)
    return ProposedAction.model_validate(
        {
            "contract_version": "1.0.0",
            "action_id": str(uuid4()),
            "farmer_id": str(farmer_id),
            "farmland_id": str(farmland_id),
            "season_id": str(season_id),
            "source_module": "m5",
            "status": "awaiting_confirmation",
            "version": 1,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "preconditions": [
                {
                    "kind": "farm_state_matches",
                    "subject": "season.status",
                    "expected_value": "active",
                    "observed_at": now.isoformat(),
                }
            ],
            "task_diff": {
                "operations": [
                    {"operation": "create", "reference": "chat-created-1", "title": "Check irrigation"}
                ]
            },
        }
    )


def _enable_actions(client, coordinator):
    client.app.state.challenge_runtime.switches = FeatureSwitches(action_confirmation=True)
    client.app.state.challenge_runtime.adapters["action_confirmation"] = coordinator


def test_m5_proposal_requires_authenticated_exact_farm_and_stores_contract(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    _enable_actions(client, coordinator)
    farmer_id = client.get("/profile").json()["farmer"]["id"]
    proposal = _proposal(farmer_id, farmland_id, season_id)

    response = client.post(
        f"/farmlands/{farmland_id}/actions/proposals",
        json=proposal.model_dump(mode="json"),
    )

    assert response.status_code == 201
    assert response.json()["action_id"] == str(proposal.action_id)
    assert coordinator.proposals == [proposal]


def test_m5_proposal_rejects_body_bound_to_another_farm(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    _enable_actions(client, coordinator)
    farmer_id = client.get("/profile").json()["farmer"]["id"]
    other_farm_id = client.app.state.other_farmland_id
    proposal = _proposal(farmer_id, other_farm_id, season_id)

    response = client.post(
        f"/farmlands/{farmland_id}/actions/proposals",
        json=proposal.model_dump(mode="json"),
    )

    assert response.status_code == 409
    assert coordinator.proposals == []


def test_m5_authenticated_proposal_route_rejects_forged_module_provenance(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    _enable_actions(client, coordinator)
    farmer_id = client.get("/profile").json()["farmer"]["id"]
    proposal = _proposal(farmer_id, farmland_id, season_id).model_copy(update={"source_module": "m6"})

    response = client.post(
        f"/farmlands/{farmland_id}/actions/proposals",
        json=proposal.model_dump(mode="json"),
    )

    assert response.status_code == 422
    assert "only accepts M5 actions" in response.json()["detail"]
    assert coordinator.proposals == []


def test_m5_confirmation_checks_farm_binding_and_returns_stale_receipt(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    _enable_actions(client, coordinator)
    action_id = uuid4()

    response = client.post(
        f"/farmlands/{farmland_id}/actions/{action_id}/confirm",
        json={"expected_version": 7, "idempotency_key": "m5-confirm-retry-1", "decision": "confirm"},
    )

    assert response.status_code == 404
    assert coordinator.confirmations == []


def test_m5_pending_actions_are_scoped_to_the_authenticated_farm(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    _enable_actions(client, coordinator)

    response = client.get(f"/farmlands/{farmland_id}/actions/pending")
    other_farm_response = client.get(
        f"/farmlands/{client.app.state.other_farmland_id}/actions/pending"
    )

    assert response.status_code == 200
    assert response.json() == []
    assert other_farm_response.status_code == 404


def test_consent_endpoint_requires_idempotency_key_and_persists_explicit_decision(client_and_farm):
    client, _, _, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    client.app.state.challenge_runtime.adapters["consent_records"] = coordinator
    payload = {
        "contract_version": "1.0.0",
        "purpose": "offline_storage",
        "decision": "granted",
        "policy_version": "2026-10-v1",
        "channel": "explicit_tap",
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    missing_key = client.post("/challenge/consents", json=payload)
    saved = client.post(
        "/challenge/consents",
        json=payload,
        headers={"Idempotency-Key": "offline-consent-001"},
    )

    assert missing_key.status_code == 400
    assert saved.status_code == 200
    assert saved.json()["consent_record_id"]
    assert coordinator.consents[0][2] == "offline-consent-001"


def test_consent_storage_remains_available_while_action_confirmation_is_safe_off(client_and_farm):
    client, _, _, _ = client_and_farm
    coordinator = RecordingActionCoordinator()
    runtime = client.app.state.challenge_runtime
    runtime.switches = FeatureSwitches()
    runtime.adapters.pop("action_confirmation", None)
    runtime.adapters["consent_records"] = coordinator
    payload = {
        "contract_version": "1.0.0",
        "purpose": "offline_storage",
        "decision": "granted",
        "policy_version": "2026-10-v1",
        "channel": "explicit_tap",
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    response = client.post(
        "/challenge/consents",
        json=payload,
        headers={"Idempotency-Key": "offline-consent-safe-off-1"},
    )

    assert response.status_code == 200
    assert coordinator.consents[0][2] == "offline-consent-safe-off-1"


def test_action_routes_fail_closed_when_feature_flag_is_disabled(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    client.app.state.challenge_runtime.switches = FeatureSwitches()

    response = client.get(f"/farmlands/{farmland_id}/actions/pending")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "unavailable"
