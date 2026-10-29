from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.challenge.v1 import (
    ActionExecutionReceipt,
    AdaptiveRecommendation,
    ConsentRecordInput,
    ClimateVariableCoverage,
    DistrictClimateBundle,
    DistrictClimateBundleManifest,
    DiseaseProblemSyncRequest,
    FarmProfileSnapshot,
    PlantingWindowAdvisory,
    ProposedAction,
    RotationComparison,
    SourceProvenance,
    TaskDiff,
)


def test_profile_snapshot_carries_owner_context_and_separate_provenance():
    farm_id = uuid4()
    owner_id = uuid4()
    captured_at = datetime(2026, 10, 29, 3, tzinfo=timezone.utc)
    profile = FarmProfileSnapshot.model_validate(
        {
            "contract_version": "1.0.0",
            "farmland_id": farm_id,
            "farmer_id": owner_id,
            "captured_at": captured_at,
            "profile": {
                "district_code": "SYN-81",
                "division": "SYNTHETIC DIVISION",
                "district": "SYNTHETIC DISTRICT",
                "upazila": "Paba",
                "village_or_locality": "SYNTHETIC LOCALITY",
                "land_area_sqm": 4000,
                "area_unit": "square_metre",
                "soil_type": "loam",
                "land_type": "medium_high",
                "irrigation_available": True,
                "water_source": "canal",
                "equipment": ["power_tiller"],
                "budget_amount": 25000,
                "budget_currency": "BDT",
            },
            "active_season": None,
            "crop_priorities": [],
            "rotation_history": [],
            "provenance": [
                {
                    "source_id": "farmer:profile",
                    "source_name": "SYNTHETIC TEST ONLY — farmer profile",
                    "retrieved_at": captured_at,
                    "recorded_at": captured_at,
                    "method": "farmer_input",
                    "quality_status": "synthetic",
                }
            ],
        }
    )

    assert profile.farmland_id == farm_id
    assert profile.profile.village_or_locality == "SYNTHETIC LOCALITY"
    assert profile.profile.area_unit == "square_metre"
    assert profile.provenance[0].method == "farmer_input"


def test_climate_bundle_rejects_unknown_units_and_unaligned_series():
    manifest = DistrictClimateBundleManifest.model_validate(
        {
            "contract_version": "1.0.0",
            "district_code": "BD-81",
            "bundle_id": "bd-81-2026-v1",
            "created_at": "2026-10-29T00:00:00Z",
            "coverage_start": "2026-10-01",
            "coverage_end": "2026-10-02",
            "assets": [],
        }
    )
    bundle = DistrictClimateBundle.model_validate(
        {
            "contract_version": "1.0.0",
            "manifest": manifest.model_dump(mode="json"),
            "daily_series": [
                {
                    "date": "2026-10-01",
                    "rainfall_mm": 4.2,
                    "temperature_c": 28.1,
                    "solar_mj_m2_day": 18.0,
                },
                {
                    "date": "2026-10-02",
                    "rainfall_mm": 0,
                    "temperature_c": 28.4,
                    "solar_mj_m2_day": 19.2,
                },
            ],
        }
    )

    assert len(bundle.daily_series) == 2
    assert bundle.daily_series[0].rainfall_mm == 4.2

    assert ClimateVariableCoverage(
        variable="rainfall",
        units="mm/day",
        status="partial",
        expected_observations=25,
        valid_observations=24,
        missing_observations=1,
    ).missing_observations == 1
    with pytest.raises(ValidationError, match="equal expected observations"):
        ClimateVariableCoverage(
            variable="rainfall",
            units="mm/day",
            status="available",
            expected_observations=25,
            valid_observations=24,
            missing_observations=0,
        )

    bad_series = bundle.model_dump(mode="json")
    bad_series["daily_series"][1]["date"] = "2026-10-01"
    with pytest.raises(ValidationError, match="strictly increasing"):
        DistrictClimateBundle.model_validate(bad_series)


def test_advisory_and_rotation_outputs_are_evidence_backed_and_bounded():
    provenance = SourceProvenance.model_validate(
        {
            "source_id": "nasa-power:bd-81:2026",
            "source_name": "SYNTHETIC TEST ONLY",
            "source_url": None,
            "dataset_version": "fixture-v1",
            "retrieved_at": "2026-10-29T00:00:00Z",
            "recorded_at": "2026-10-29T00:00:00Z",
            "method": "manual_entry",
            "license": "Synthetic test data",
            "quality_status": "synthetic",
        }
    )
    advisory = PlantingWindowAdvisory.model_validate(
        {
            "contract_version": "1.0.0",
            "status": "available",
            "district_code": "SYN-81",
            "crop_code": "SYNTHETIC AMAN RICE",
            "onset_shift_days": 11,
            "comparison": {
                "baseline_years": list(range(2001, 2013)),
                "recent_years": list(range(2013, 2026)),
                "baseline_onset_days": [180, 182, 179, 181, 184, 177, 183, 180, 186, 178, 182, 185],
                "recent_onset_days": [190, 193, 188, 191, 195, 189, 192, 187, 194, 190, 196, 188, 193],
                "test_name": "mann_whitney_u",
                "test_statistic": 9.0,
                "p_value": 0.08,
            },
            "recommended_window": {"start": "2026-07-01", "end": "2026-07-12"},
            "advice_bn": "বৃষ্টির শুরুর জন্য জমি প্রস্তুত রাখুন।",
            "advice_en": "Prepare the field for the expected rain onset.",
            "sms_summary": "বৃষ্টি দেরিতে আসতে পারে; জমি প্রস্তুত রাখুন।",
            "assumptions": ["Usable-rain onset uses the displayed 20 mm rule."],
            "provenance": [provenance.model_dump(mode="json")],
            "created_at": "2026-10-29T00:00:00Z",
        }
    )
    rotation = RotationComparison.model_validate(
        {
            "contract_version": "1.0.0",
            "farmland_id": str(uuid4()),
            "current_sequence": ["rice_aman", "lentil"],
            "alternatives": [["rice_aman", "mustard"], ["rice_aman", "maize"]],
            "evidence": [provenance.model_dump(mode="json")],
            "created_at": "2026-10-29T00:00:00Z",
        }
    )

    assert advisory.onset_shift_days == 11
    assert len(advisory.comparison.baseline_years) == 12
    assert len(advisory.comparison.recent_years) == 13
    assert len(advisory.sms_summary) <= 160
    assert len(rotation.alternatives) == 2

    invalid = advisory.model_dump(mode="json")
    invalid["sms_summary"] = "x" * 161
    with pytest.raises(ValidationError):
        PlantingWindowAdvisory.model_validate(invalid)


def test_adaptive_recommendation_exposes_unknowns_and_constraints():
    recommendation = AdaptiveRecommendation.model_validate(
        {
            "contract_version": "1.0.0",
            "farmland_id": str(uuid4()),
            "decision_question": "Can the farmer plant this crop now?",
            "answer_status": "insufficient_evidence",
            "recommendation_code": None,
            "confidence": None,
            "constraints": ["No current soil test is available."],
            "unknowns": ["Soil nutrient status"],
            "evidence_refs": [],
            "created_at": "2026-10-29T00:00:00Z",
        }
    )

    assert recommendation.recommendation_code is None
    assert recommendation.confidence is None
    assert recommendation.unknowns


def test_proposed_action_requires_expiry_and_idempotent_change_reference():
    action = ProposedAction.model_validate(
        {
            "contract_version": "1.0.0",
            "action_id": str(uuid4()),
            "farmer_id": str(uuid4()),
            "farmland_id": str(uuid4()),
            "source_module": "m2",
            "status": "awaiting_confirmation",
            "version": 1,
            "created_at": "2026-10-29T00:00:00Z",
            "expires_at": "2026-10-30T00:00:00Z",
            "preconditions": [
                {
                    "kind": "farm_state_matches",
                    "subject": "season.current_crop_code",
                    "expected_value": "rice_aman",
                    "observed_at": "2026-10-29T00:00:00Z",
                }
            ],
            "task_diff": {
                "operations": [
                    {
                        "operation": "create",
                        "reference": "action-create-drainage",
                        "title": "Clear field drainage",
                        "priority": "high",
                    }
                ]
            },
            "required_consent_purposes": ["adaptive_recommendations"],
        }
    )

    assert action.task_diff.operations[0].reference == "action-create-drainage"
    assert action.status == "awaiting_confirmation"
    with pytest.raises(ValidationError):
        TaskDiff.model_validate(
            {"operations": [{"operation": "create", "title": "No stable reference"}]}
        )


def test_action_receipt_carries_replay_safe_outcome_and_version():
    receipt = ActionExecutionReceipt.model_validate(
        {
            "contract_version": "1.0.0",
            "receipt_id": str(uuid4()),
            "action_id": str(uuid4()),
            "farmer_id": str(uuid4()),
            "idempotency_key": "confirm-12345678",
            "action_version": 2,
            "status": "applied",
            "created_at": "2026-10-29T00:00:00Z",
            "completed_at": "2026-10-29T00:00:01Z",
            "result": {"created_task_ids": [str(uuid4())]},
        }
    )

    assert receipt.action_version == 2
    assert receipt.status == "applied"


def test_consent_is_versioned_and_disease_sync_never_assumes_confirmation():
    consent = ConsentRecordInput.model_validate(
        {
            "contract_version": "1.0.0",
            "purpose": "disease_problem_sync",
            "decision": "granted",
            "policy_version": "2026-10-v1",
            "channel": "explicit_tap",
            "captured_at": "2026-10-29T00:00:00Z",
        }
    )
    request = DiseaseProblemSyncRequest.model_validate(
        {
            "contract_version": "1.0.0",
            "disease_result_id": str(uuid4()),
            "farmland_id": str(uuid4()),
            "idempotency_key": "scan-sync-12345678",
            "mode": "deferred_confirmation",
            "assessment": "possible_issue",
            "possible_issue": "possible_leaf_spot",
            "confidence": 0.82,
            "farmer_confirmation": "pending",
            "consent_receipt_id": None,
            "symptoms": None,
            "requested_at": "2026-10-29T00:00:00Z",
        }
    )

    assert consent.decision == "granted"
    assert request.farmer_confirmation == "pending"
    assert request.symptoms is None

    for confirmation, consent_id in (("not_required", None), ("confirmed", None)):
        body = request.model_dump(mode="json")
        body["farmer_confirmation"] = confirmation
        body["consent_receipt_id"] = consent_id
        with pytest.raises(ValidationError):
            DiseaseProblemSyncRequest.model_validate(body)


def test_source_provenance_requires_aware_timestamps_and_valid_checksum():
    base = {
        "source_id": "dataset-1",
        "source_name": "NASA POWER",
        "retrieved_at": datetime(2026, 10, 29),
        "recorded_at": datetime(2026, 10, 29, tzinfo=timezone.utc),
        "method": "satellite_reanalysis",
        "checksum_sha256": "not-a-sha256",
    }

    with pytest.raises(ValidationError):
        SourceProvenance.model_validate(base)

    with pytest.raises(ValidationError):
        SourceProvenance.model_validate({**base, "retrieved_at": datetime.now(timezone.utc)})


def test_contract_catalog_has_explicit_version_for_generated_consumers():
    from app.contracts.challenge.v1 import CONTRACT_VERSION, ContractCatalog

    catalog = ContractCatalog.model_validate(
        {"contract_version": CONTRACT_VERSION}
    )
    assert catalog.contract_version == "1.0.0"
