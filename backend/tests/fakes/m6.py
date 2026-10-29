import hashlib
import json
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from app.contracts.challenge.ports import AdapterConflict, AdapterUnavailable
from app.contracts.challenge.v1 import DiseaseProblemSyncReceipt


class FakeDiseaseProblemSyncProvider:
    """Deferred M6 fake; records no problem until explicit confirmation + consent."""

    def __init__(self, *, failure=False):
        self.failure = failure
        self.requests = {}
        self.problem_by_result = {}

    def request_sync(self, request):
        if self.failure:
            raise AdapterUnavailable("synthetic Module 3 sync failure")
        key = (request.farmland_id, request.idempotency_key)
        fingerprint = hashlib.sha256(
            json.dumps(request.model_dump(mode="json"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        previous = self.requests.get(key)
        if previous:
            old_fingerprint, receipt = previous
            if old_fingerprint != fingerprint:
                raise AdapterConflict("synthetic sync idempotency key reuse")
            return receipt

        problem_id = self.problem_by_result.get(request.disease_result_id)
        if request.assessment in {"healthy", "uncertain"} or request.farmer_confirmation == "denied":
            status, retriable = "no_problem", False
            problem_id = None
        elif request.confidence is None or request.confidence < 0.70:
            status, retriable = "ineligible", False
            problem_id = None
        elif request.farmer_confirmation == "pending":
            status, retriable = "awaiting_confirmation", False
            problem_id = None
        elif request.farmer_confirmation == "confirmed" and request.consent_receipt_id:
            status, retriable = "synchronized", False
            if problem_id is None:
                problem_id = uuid5(NAMESPACE_URL, f"synthetic-problem:{request.disease_result_id}")
                self.problem_by_result[request.disease_result_id] = problem_id
        else:
            status, retriable = "ineligible", False
            problem_id = None

        now = datetime(2026, 10, 29, tzinfo=timezone.utc)
        receipt = DiseaseProblemSyncReceipt(
            contract_version="1.0.0",
            disease_result_id=request.disease_result_id,
            farmland_id=request.farmland_id,
            status=status,
            problem_id=problem_id,
            retriable=retriable,
            created_at=now,
        )
        self.requests[key] = (fingerprint, receipt)
        return receipt
