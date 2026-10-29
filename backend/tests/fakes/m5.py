from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from app.contracts.challenge.ports import AdapterConflict, AdapterUnavailable
from app.contracts.challenge.v1 import ActionExecutionReceipt


class FakeActionConfirmationProvider:
    """Deterministic confirmation fake for replay, conflict, and failure cases."""

    def __init__(self, *, failure=False):
        self.failure = failure
        self.proposals = {}
        self.receipts = {}

    def propose(self, proposal):
        self.proposals[proposal.action_id] = proposal
        return proposal

    def confirm(self, farmer_id, action_id, expected_version, idempotency_key, *, decision="confirm"):
        if self.failure:
            raise AdapterUnavailable("synthetic action service failure")
        proposal = self.proposals.get(action_id)
        if proposal is None or proposal.farmer_id != farmer_id:
            raise AdapterConflict("synthetic proposal is unavailable")
        fingerprint = (farmer_id, action_id, expected_version, decision)
        existing = self.receipts.get((farmer_id, idempotency_key))
        if existing:
            old_fingerprint, receipt = existing
            if old_fingerprint != fingerprint:
                raise AdapterConflict("synthetic idempotency key reuse")
            return receipt
        status = "applied" if expected_version == proposal.version and decision == "confirm" else "conflict"
        now = datetime(2026, 10, 29, tzinfo=timezone.utc)
        receipt = ActionExecutionReceipt(
            contract_version="1.0.0",
            receipt_id=uuid5(NAMESPACE_URL, f"{farmer_id}:{idempotency_key}"),
            action_id=action_id,
            farmer_id=farmer_id,
            idempotency_key=idempotency_key,
            action_version=expected_version,
            status=status,
            created_at=now,
            completed_at=now,
            result={"synthetic": True},
        )
        self.receipts[(farmer_id, idempotency_key)] = (fingerprint, receipt)
        return receipt
