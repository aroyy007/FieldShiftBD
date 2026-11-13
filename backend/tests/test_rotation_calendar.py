from datetime import date


def _candidate(*steps):
    from app.services.rotation.catalog import RotationCandidate, RotationCandidateStep

    return RotationCandidate(
        candidate_id="synthetic-test", role="alternative", district_code="5081",
        steps=tuple(RotationCandidateStep(**step) for step in steps),
        source_ids=("synthetic-source",), review_status="source_verified_pending_agronomy_review",
        applicability="unknown",
    )


def test_aman_to_rabi_sequence_rolls_across_december_without_overlap():
    from app.services.rotation.catalog import CropWindow
    from src.compute.rotation_calendar import evaluate_calendar

    result = evaluate_calendar(_candidate(
        {"crop_code": "rice", "season_code": "aman", "event_basis": "transplant_to_harvest",
         "window": CropWindow(start="07-25", end="11-14"), "source_ids": ("aman-source",)},
        {"crop_code": "chickpea", "season_code": "rabi", "event_basis": "sow_to_harvest",
         "window": CropWindow(start="12-01", end="03-15"), "source_ids": ("rabi-source",)},
    ), 2026, rules=None)
    assert result.status == "needs_turnaround_rule"
    assert result.windows[1].start_date == date(2026, 12, 1)
    assert result.windows[1].end_date == date(2027, 3, 15)


def test_incompatible_crop_intervals_are_not_feasible():
    from app.services.rotation.catalog import CropWindow
    from src.compute.rotation_calendar import evaluate_calendar

    result = evaluate_calendar(_candidate(
        {"crop_code": "rice", "season_code": "aman", "event_basis": "transplant_to_harvest",
         "window": CropWindow(start="07-25", end="12-10"), "source_ids": ("aman-source",)},
        {"crop_code": "wheat", "season_code": "rabi", "event_basis": "sow_to_harvest",
         "window": CropWindow(start="11-20", end="03-15"), "source_ids": ("wheat-source",)},
    ), 2026, rules=None)
    assert result.status == "overlap"


def test_turnaround_number_without_reviewed_source_cannot_establish_feasibility():
    from app.services.rotation.catalog import CropWindow, ReviewedRuleSet
    from src.compute.rotation_calendar import evaluate_calendar

    candidate = _candidate(
        {"crop_code": "rice", "season_code": "aman", "event_basis": "transplant_to_harvest",
         "window": CropWindow(start="07-25", end="11-14"), "source_ids": ("aman-source",)},
        {"crop_code": "wheat", "season_code": "rabi", "event_basis": "sow_to_harvest",
         "window": CropWindow(start="12-01", end="03-15"), "source_ids": ("wheat-source",)},
    )
    assert evaluate_calendar(candidate, 2026, rules=None).status == "needs_turnaround_rule"
    unsupported = ReviewedRuleSet(minimum_turnaround_days=7, source_ids=(), review_status="unreviewed")
    assert evaluate_calendar(candidate, 2026, rules=unsupported).status == "needs_turnaround_rule"
    reviewed = ReviewedRuleSet(minimum_turnaround_days=7, source_ids=("reviewed-rule",), review_status="reviewed")
    assert evaluate_calendar(candidate, 2026, rules=reviewed).status == "feasible"


def test_leap_day_windows_are_only_expanded_in_leap_years_and_gdd_stays_unknown():
    from app.services.rotation.catalog import CropWindow
    from src.compute.rotation_calendar import evaluate_calendar

    candidate = _candidate({"crop_code": "rice", "season_code": "aman", "event_basis": "source_window",
                            "window": CropWindow(start="02-29", end="03-20"), "source_ids": ("calendar",)})
    assert evaluate_calendar(candidate, 2027, rules=None).status == "insufficient_dates"
    leap_result = evaluate_calendar(candidate, 2028, rules=None)
    assert leap_result.status == "feasible"
    assert leap_result.windows[0].start_date == date(2028, 2, 29)
    assert leap_result.gdd_summary is None
