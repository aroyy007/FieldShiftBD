"""Agricultural knowledge provider tests with synthetic-only fixtures."""

from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
pytest.importorskip("sqlalchemy", reason="M2 knowledge tests require backend dependencies from backend/requirements.txt")

from app.services.m2_knowledge import (
    EvidenceStatus,
    KnowledgeQuery,
    get_relevant_evidence,
)


CROP_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CROP_ID = UUID("88888888-8888-4888-8888-888888888888")
VARIETY_ID = UUID("99999999-9999-4999-8999-999999999999")
AS_OF = date(2026, 10, 6)


class KnowledgeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None

    def scalars(self, statement):
        self.statement = statement
        # Return all records to exercise the provider's defense-in-depth filters.
        return iter(self.rows)


def synthetic_row(**overrides):
    values = {
        "id": uuid4(),
        "crop_id": CROP_ID,
        "crop_variety_id": None,
        "category": "soil_factor",
        "region_code": None,
        "content": {
            "source_type": "synthetic_test_fixture",
            "factor": "synthetic soil factor",
            "applicability": {"soil_type": "synthetic loam"},
            "evidence": {"description": "Synthetic evidence for provider tests only."},
            "suitable_because": [{
                "factor": "soil",
                "explanation": "Synthetic statement, never agricultural advice.",
                "when": {"soil_type": "synthetic loam"},
            }],
        },
        "source_name": "SYNTHETIC TEST FIXTURE — NOT AGRICULTURAL ADVICE",
        "source_reference": "test-fixture-only",
        "review_status": "approved",
        "reviewed_by": uuid4(),
        "reviewed_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2027, 1, 1),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def query(**overrides):
    values = {
        "crop_id": CROP_ID,
        "context": {"soil_type": "synthetic loam"},
        "as_of": AS_OF,
    }
    values.update(overrides)
    return KnowledgeQuery(**values)


def test_approved_effective_knowledge_is_returned_with_provenance():
    row = synthetic_row()
    result = get_relevant_evidence(KnowledgeSession([row]), query())

    assert result.status == EvidenceStatus.AVAILABLE
    assert len(result.items) == 1
    item = result.items[0]
    assert item.id == row.id
    assert item.crop_id == CROP_ID
    assert item.factor == "synthetic soil factor"
    assert item.value == row.content["evidence"]
    assert item.source_name == row.source_name
    assert item.source_type == "synthetic_test_fixture"
    assert item.source_reference == "test-fixture-only"
    assert item.review_status == "approved"
    assert item.reviewed_by == row.reviewed_by
    assert item.reviewed_at == row.reviewed_at
    assert item.effective_from == row.effective_from
    assert item.effective_to == row.effective_to


@pytest.mark.parametrize("review_status", ["draft", "in_review", "rejected"])
def test_unapproved_knowledge_is_excluded(review_status):
    row = synthetic_row(review_status=review_status)
    result = get_relevant_evidence(KnowledgeSession([row]), query())
    assert result.items == ()
    assert result.status == EvidenceStatus.MISSING_EVIDENCE


def test_approved_row_without_human_reviewer_requires_valid_source_policy():
    row = synthetic_row(reviewed_by=None, reviewed_at=None)
    result = get_relevant_evidence(KnowledgeSession([row]), query())

    assert result.items == ()
    assert result.status == EvidenceStatus.MISSING_EVIDENCE


@pytest.mark.parametrize(
    "effective_from,effective_to",
    [(date(2020, 1, 1), date(2026, 10, 5)), (date(2026, 10, 7), date(2027, 1, 1))],
)
def test_expired_or_future_knowledge_is_excluded(effective_from, effective_to):
    row = synthetic_row(effective_from=effective_from, effective_to=effective_to)
    assert get_relevant_evidence(KnowledgeSession([row]), query()).items == ()


def test_crop_and_variety_specific_filtering_includes_only_applicable_records():
    generic = synthetic_row()
    same_crop_variety = synthetic_row(crop_variety_id=VARIETY_ID)
    wrong_crop = synthetic_row(crop_id=OTHER_CROP_ID)
    wrong_variety = synthetic_row(crop_variety_id=uuid4())

    without_variety = get_relevant_evidence(
        KnowledgeSession([generic, same_crop_variety, wrong_crop, wrong_variety]), query()
    )
    assert [item.id for item in without_variety.items] == [generic.id]

    with_variety = get_relevant_evidence(
        KnowledgeSession([generic, same_crop_variety, wrong_crop, wrong_variety]),
        query(crop_variety_id=VARIETY_ID),
    )
    assert {item.id for item in with_variety.items} == {generic.id, same_crop_variety.id}


def test_region_and_context_conditions_filter_evidence():
    matching = synthetic_row(region_code="REGION-TEST")
    wrong_region = synthetic_row(region_code="OTHER-TEST")
    wrong_context = synthetic_row(content={
        **synthetic_row().content,
        "applicability": {"soil_type": "different synthetic context"},
    })
    result = get_relevant_evidence(
        KnowledgeSession([matching, wrong_region, wrong_context]),
        query(region_codes=frozenset({"region-test"})),
    )
    assert [item.id for item in result.items] == [matching.id]


def test_factor_category_filter_excludes_irrelevant_evidence():
    soil = synthetic_row(category="soil_factor")
    irrigation = synthetic_row(category="irrigation_factor")
    result = get_relevant_evidence(
        KnowledgeSession([soil, irrigation]),
        query(factor="soil_factor"),
    )
    assert [item.id for item in result.items] == [soil.id]


def test_missing_source_type_and_missing_context_fail_closed():
    no_source_type = synthetic_row(content={"evidence": "untyped synthetic text"})
    missing_context = synthetic_row()
    result = get_relevant_evidence(
        KnowledgeSession([no_source_type, missing_context]),
        query(context={}),
    )
    assert result.status == EvidenceStatus.MISSING_EVIDENCE
    assert result.items == ()


def test_missing_evidence_result_is_explicit():
    result = get_relevant_evidence(KnowledgeSession([]), query())
    assert result.status == EvidenceStatus.MISSING_EVIDENCE
    assert result.message == "No approved, currently effective evidence applies to this crop and context."
