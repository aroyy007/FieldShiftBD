"""Machine-verifiable acceptance for public BARC source snapshots."""

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
from uuid import UUID

import pytest

pytest.importorskip("sqlalchemy", reason="M2 source policy tests require backend dependencies")

from app.services.m2_source_policy import (
    BARC_POLICY_ID,
    SourcePolicyError,
    build_barc_knowledge_record,
    is_valid_automated_acceptance,
)
from app.services.m2_knowledge import EvidenceStatus, KnowledgeQuery, get_relevant_evidence
from app.services.m2_advisor import _knowledge_ref


CROP_ID = UUID("33333333-3333-4333-8333-333333333333")
RETRIEVED_ON = date(2026, 10, 7)


def snapshot():
    path = Path(__file__).resolve().parents[1] / "app" / "data" / "m2_knowledge_sources" / "barc_potato_comilla_snapshot.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_official_barc_snapshot_is_accepted_without_fabricating_a_reviewer():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)

    assert row.review_status == "approved"
    assert row.reviewed_by is None
    assert row.reviewed_at is None
    assert row.effective_from == RETRIEVED_ON
    assert row.effective_to == RETRIEVED_ON + timedelta(days=180)
    assert row.region_code == "Comilla"
    assert row.content["acceptance_policy"]["id"] == BARC_POLICY_ID
    assert row.content["acceptance_policy"]["method"] == "automated_source_validation"
    assert row.content["factors"]["regional_crop_zoning"]["kind"] == "regional_context"
    assert row.content["evidence"]["suitable_or_better_share_percent"] == pytest.approx(61.56, abs=0.01)
    explanation = row.content["factors"]["regional_crop_zoning"]["explanation"]
    assert "upazila-level" in explanation
    assert "not a field-level assessment" in explanation
    assert "dataset vintage is not published" in explanation


def test_source_policy_evidence_flows_through_provider_with_acceptance_provenance():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)

    class Session:
        def scalars(self, statement):
            return iter([row])

    result = get_relevant_evidence(
        Session(),
        KnowledgeQuery(
            crop_id=CROP_ID,
            crop_name="Potato",
            region_codes=frozenset({"Comilla"}),
            context={"country_code": "BD", "district": "Comilla", "upazila": "Comilla"},
            as_of=RETRIEVED_ON,
        ),
    )

    assert result.status == EvidenceStatus.AVAILABLE
    assert len(result.items) == 1
    assert result.items[0].acceptance_method == f"automated_source_policy:{BARC_POLICY_ID}:v1"
    assert _knowledge_ref(result.items[0]).acceptance_method == result.items[0].acceptance_method
    assert "not a field-level assessment" in result.items[0].content["factors"]["regional_crop_zoning"]["explanation"]


def test_source_policy_evidence_is_not_reused_for_another_crop():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)

    class Session:
        def scalars(self, statement):
            return iter([row])

    result = get_relevant_evidence(
        Session(),
        KnowledgeQuery(
            crop_id=CROP_ID,
            crop_name="Maize",
            region_codes=frozenset({"Comilla"}),
            context={"country_code": "BD", "district": "Comilla", "upazila": "Comilla"},
            as_of=RETRIEVED_ON,
        ),
    )

    assert result.status == EvidenceStatus.MISSING_EVIDENCE
    assert result.items == ()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["area_hectares"].update(suitable=11019),
        lambda value: value.update(source_url="https://example.com/fake-map"),
        lambda value: value["region"].update(upazila="Other Upazila"),
        lambda value: value.update(map_page_sha256="not-a-hash"),
        lambda value: value.update(methodology_page_sha256="A" * 64),
    ],
)
def test_source_policy_rejects_invalid_provenance_or_inconsistent_area(mutate):
    invalid = deepcopy(snapshot())
    mutate(invalid)

    with pytest.raises(SourcePolicyError):
        build_barc_knowledge_record(invalid, CROP_ID, evaluated_on=RETRIEVED_ON)


def test_source_policy_expires_snapshot_after_refresh_window():
    with pytest.raises(SourcePolicyError, match="refresh window"):
        build_barc_knowledge_record(
            snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON + timedelta(days=181)
        )


def test_runtime_rejects_accepted_record_after_regional_disclosure_is_removed():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)
    assert is_valid_automated_acceptance(row, row.content, crop_name="Potato")

    row.content["factors"]["regional_crop_zoning"]["explanation"] = (
        "Potato is a good fit for this farm."
    )

    assert not is_valid_automated_acceptance(row, row.content, crop_name="Potato")


def test_runtime_acceptance_is_bound_to_potato_without_variety_or_source_name_changes():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)
    assert is_valid_automated_acceptance(row, row.content, crop_name="Potato")
    assert not is_valid_automated_acceptance(row, row.content, crop_name="Maize")

    row.crop_variety_id = UUID("55555555-5555-4555-8555-555555555555")
    assert not is_valid_automated_acceptance(row, row.content, crop_name="Potato")

    row.crop_variety_id = None
    row.source_name = "Changed source"
    assert not is_valid_automated_acceptance(row, row.content, crop_name="Potato")


def test_runtime_policy_check_rejects_malformed_check_entries_without_raising():
    row = build_barc_knowledge_record(snapshot(), CROP_ID, evaluated_on=RETRIEVED_ON)
    row.content["acceptance_policy"]["checks_passed"] = [{"unexpected": "object"}]

    assert not is_valid_automated_acceptance(row, row.content, crop_name="Potato")
