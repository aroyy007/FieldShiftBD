from datetime import date, datetime, timezone

from app.contracts.challenge.v1 import (
    AdaptiveRecommendation,
    OnsetComparison,
    PlantingWindowAdvisory,
    RecommendedPlantingWindow,
    RotationComparison,
    RotationSequenceStep,
    RotationStrategy,
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
        alternatives = [[current, "SYNTHETIC LENTIL"], [current, "SYNTHETIC MUSTARD"]]
        strategies = [
            RotationStrategy(
                strategy_id=f"synthetic-{index}",
                name_en=f"SYNTHETIC rotation {index}",
                name_bn=f"SYNTHETIC rotation {index}",
                applicability_status="matches_documented_scope",
                documented_scope_en="SYNTHETIC test scope only",
                documented_scope_bn="SYNTHETIC test scope only",
                steps=[
                    RotationSequenceStep(
                        crop_code=current,
                        crop_name_en=current,
                        crop_name_bn=current,
                        season_code="synthetic-current",
                        season_label_en="SYNTHETIC season",
                        season_label_bn="SYNTHETIC season",
                    ),
                    RotationSequenceStep(
                        crop_code=other_crop,
                        crop_name_en=other_crop,
                        crop_name_bn=other_crop,
                        season_code="synthetic-next",
                        season_label_en="SYNTHETIC next season",
                        season_label_bn="SYNTHETIC next season",
                    ),
                ],
                evidence_ids=["synthetic-test-only"],
            )
            for index, other_crop in enumerate(("SYNTHETIC LENTIL", "SYNTHETIC MUSTARD"), start=1)
        ]
        return RotationComparison(
            contract_version="1.0.0",
            farmland_id=snapshot.farmland_id,
            current_sequence=[current],
            alternatives=alternatives,
            strategies=strategies,
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
