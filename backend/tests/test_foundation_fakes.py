from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.contracts.challenge.ports import (
    AdapterConflict,
    AdapterUnavailable,
    ArtifactNotFound,
    StaleArtifact,
)
from app.contracts.challenge.v1 import (
    DiseaseProblemSyncRequest,
    ProposedAction,
)
from app.services.profile_intake.snapshot import FarmSnapshotNotFound
from tests.fakes.m1 import FakeFarmProfileSnapshotReader
from tests.fakes.m2 import (
    FakeAdaptiveDecisionProvider,
    FakePlantingWindowAdvisor,
    FakeRotationComparisonProvider,
)
from tests.fakes.m3 import FakeTaskDiffOwnerOperation
from tests.fakes.m4 import FakeClimateScenario, FakeDistrictClimateBundleProvider
from tests.fakes.m5 import FakeActionConfirmationProvider
from tests.fakes.m6 import FakeDiseaseProblemSyncProvider

NOW = datetime(2026, 10, 29, 9, tzinfo=timezone.utc)


def _proposal(farmer_id, farm_id, season_id):
    return ProposedAction.model_validate({
        "contract_version": "1.0.0",
        "action_id": str(uuid4()),
        "farmer_id": str(farmer_id),
        "farmland_id": str(farm_id),
        "season_id": str(season_id),
        "source_module": "m2",
        "status": "awaiting_confirmation",
        "version": 1,
        "created_at": NOW.isoformat(),
        "expires_at": "2026-10-30T09:00:00Z",
        "preconditions": [{"kind": "farm_state_matches", "subject": "season.status"}],
        "task_diff": {"operations": [{"operation": "create", "reference": "test-task", "title": "SYNTHETIC TEST ONLY"}]},
    })


def _sync_request(*, assessment="possible_issue", confirmation="pending", confidence=0.9, consent=None, key=None):
    return DiseaseProblemSyncRequest.model_validate({
        "contract_version": "1.0.0",
        "disease_result_id": str(uuid4()),
        "farmland_id": str(uuid4()),
        "idempotency_key": key or f"sync-{uuid4()}",
        "mode": "deferred_confirmation",
        "assessment": assessment,
        "possible_issue": "SYNTHETIC TEST issue" if assessment == "possible_issue" else None,
        "confidence": confidence,
        "farmer_confirmation": confirmation,
        "consent_receipt_id": str(consent) if consent else None,
        "requested_at": NOW.isoformat(),
    })


def test_m1_fake_returns_only_its_own_synthetic_farm():
    adapter = FakeFarmProfileSnapshotReader()
    snapshot = adapter.get_snapshot(adapter.snapshot.farmer_id, adapter.snapshot.farmland_id)
    assert snapshot.profile.district_code == "SYN-81"
    assert snapshot.provenance[0].quality_status == "synthetic"
    with pytest.raises(FarmSnapshotNotFound):
        adapter.get_snapshot(uuid4(), snapshot.farmland_id)


@pytest.mark.parametrize(
    ("scenario", "error"),
    [
        (FakeClimateScenario.UNKNOWN, ArtifactNotFound),
        (FakeClimateScenario.EXPIRED, StaleArtifact),
        (FakeClimateScenario.CONFLICT, AdapterConflict),
        (FakeClimateScenario.FAILURE, AdapterUnavailable),
    ],
)
def test_m4_fake_exposes_unavailable_and_conflict_states(scenario, error):
    adapter = FakeDistrictClimateBundleProvider(scenario)
    if scenario == FakeClimateScenario.SUPPORTED:
        pytest.fail("the parameter table must cover only non-supported scenarios")
    with pytest.raises(error):
        adapter.get_bundle("SYN-81", as_of=NOW)


def test_m4_m2_advisor_outputs_keep_synthetic_provenance_and_uncertainty():
    profile = FakeFarmProfileSnapshotReader().snapshot
    climate = FakeDistrictClimateBundleProvider().get_bundle("SYN-81", as_of=NOW)
    advisory = FakePlantingWindowAdvisor().advise(profile, climate, "SYNTHETIC RICE")
    rotation = FakeRotationComparisonProvider().compare(profile)
    adaptive = FakeAdaptiveDecisionProvider().evaluate(profile, "SYNTHETIC QUESTION")

    assert advisory.status == "available"
    assert advisory.provenance[0].quality_status == "synthetic"
    assert advisory.comparison.baseline_years == list(range(2001, 2013))
    assert rotation.evidence[0].quality_status == "synthetic"
    assert adaptive.answer_status == "insufficient_evidence"
    assert adaptive.recommendation_code is None


def test_m3_task_diff_fake_uses_idempotent_typed_owner_result():
    profile = FakeFarmProfileSnapshotReader().snapshot
    action = _proposal(profile.farmer_id, profile.farmland_id, uuid4())
    fake = FakeTaskDiffOwnerOperation()
    first = fake.apply(None, action, action.task_diff, now=NOW)
    replay = fake.apply(None, action, action.task_diff, now=NOW)

    assert first.created_task_ids == replay.created_task_ids
    assert first.action_id == action.action_id
    assert len(fake.tasks) == 1


def test_m5_fake_replays_receipt_and_rejects_idempotency_key_reuse():
    profile = FakeFarmProfileSnapshotReader().snapshot
    proposal = _proposal(profile.farmer_id, profile.farmland_id, uuid4())
    fake = FakeActionConfirmationProvider()
    fake.propose(proposal)
    first = fake.confirm(profile.farmer_id, proposal.action_id, 1, "m5-confirm-test")
    replay = fake.confirm(profile.farmer_id, proposal.action_id, 1, "m5-confirm-test")
    assert first.receipt_id == replay.receipt_id
    with pytest.raises(AdapterConflict):
        fake.confirm(profile.farmer_id, proposal.action_id, 1, "m5-confirm-test", decision="reject")


def test_m6_fake_requires_confidence_explicit_confirmation_and_consent():
    fake = FakeDiseaseProblemSyncProvider()

    healthy = fake.request_sync(_sync_request(assessment="healthy", confirmation="not_required", confidence=None))
    uncertain = fake.request_sync(_sync_request(assessment="uncertain", confirmation="not_required", confidence=None))
    low_confidence = fake.request_sync(_sync_request(confidence=0.69))
    pending = fake.request_sync(_sync_request(confirmation="pending", confidence=0.9))
    denied = fake.request_sync(_sync_request(confirmation="denied", confidence=0.9))
    assert [healthy.status, uncertain.status] == ["no_problem", "no_problem"]
    assert low_confidence.status == "ineligible" and low_confidence.problem_id is None
    assert pending.status == "awaiting_confirmation" and pending.problem_id is None
    assert denied.status == "no_problem" and denied.problem_id is None

    issue = _sync_request(confirmation="confirmed", confidence=0.9, consent=uuid4())
    first = fake.request_sync(issue)
    assert first.status == "synchronized"
    assert first.problem_id is not None
    new_key_retry = issue.model_copy(update={"idempotency_key": f"retry-{uuid4()}"})
    replayed_problem = fake.request_sync(new_key_retry)
    assert replayed_problem.problem_id == first.problem_id
    assert replayed_problem.status == "synchronized"


def test_m6_fake_failure_is_explicit_and_retriable_by_caller():
    with pytest.raises(AdapterUnavailable):
        FakeDiseaseProblemSyncProvider(failure=True).request_sync(_sync_request())
