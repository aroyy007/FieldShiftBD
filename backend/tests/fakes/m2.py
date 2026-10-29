from datetime import date, datetime, timezone

from app.contracts.challenge.v1 import (
    AdaptiveRecommendation,
    OnsetComparison,
    PlantingWindowAdvisory,
    RecommendedPlantingWindow,
    RotationComparison,
    SourceProvenance,
)

SYNTHETIC_PROVENANCE = SourceProvenance(
    source_id="synthetic-advisor-fixture-v1",
    source_name="SYNTHETIC TEST ONLY — advisor fixture",
    dataset_version="fixture-v1",
    retrieved_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
    recorded_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
    method="manual_entry",
    license="Synthetic test data",
    quality_status="synthetic",
)


class FakePlantingWindowAdvisor:
    def advise(self, snapshot, bundle, crop_code):
        return PlantingWindowAdvisory(
            contract_version="1.0.0",
            status="available",
            district_code=bundle.manifest.district_code,
            crop_code=crop_code,
            onset_shift_days=11,
            comparison=OnsetComparison(
                baseline_years=list(range(2001, 2013)),
                recent_years=list(range(2013, 2026)),
                baseline_onset_days=[180] * 12,
                recent_onset_days=[191] * 13,
                test_name="mann_whitney_u",
                test_statistic=78,
                p_value=0.2,
            ),
            recommended_window=RecommendedPlantingWindow(
                start=date(2026, 7, 1), end=date(2026, 7, 12)
            ),
            advice_bn="SYNTHETIC TEST: জমি প্রস্তুত রাখুন।",
            advice_en="SYNTHETIC TEST: prepare the field.",
            sms_summary="SYNTHETIC TEST: prepare the field.",
            assumptions=["Synthetic fixture only; not agronomic advice."],
            provenance=[SYNTHETIC_PROVENANCE],
            created_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
        )


class FakeRotationComparisonProvider:
    def compare(self, snapshot):
        current = snapshot.active_season.crop_code if snapshot.active_season else "SYNTHETIC CROP"
        return RotationComparison(
            contract_version="1.0.0",
            farmland_id=snapshot.farmland_id,
            current_sequence=[current],
            alternatives=[[current, "SYNTHETIC LENTIL"], [current, "SYNTHETIC MUSTARD"]],
            evidence=[SYNTHETIC_PROVENANCE],
            created_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
        )


class FakeAdaptiveDecisionProvider:
    def evaluate(self, snapshot, question):
        return AdaptiveRecommendation(
            contract_version="1.0.0",
            farmland_id=snapshot.farmland_id,
            decision_question=question,
            answer_status="insufficient_evidence",
            recommendation_code=None,
            confidence=None,
            constraints=["SYNTHETIC TEST: no live evidence was loaded."],
            unknowns=["SYNTHETIC soil test"],
            evidence_refs=[],
            created_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
        )
