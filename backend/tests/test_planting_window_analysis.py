from datetime import date, timedelta

from app.services.planting_window_analysis import compare_annual_onsets


def test_compares_fixed_periods_and_reports_threshold_sensitivity():
    rainfall = {}
    for year in range(2001, 2026):
        onset_day = 10 if year <= 2012 else 20
        start = date(year, 6, 1)
        for offset in range(45):
            rainfall[start + timedelta(days=offset)] = 0.0
        for offset in range(onset_day, onset_day + 7):
            rainfall[start + timedelta(days=offset)] = 4.0
        rainfall[start + timedelta(days=onset_day + 9)] = 2.0
        rainfall[start + timedelta(days=onset_day + 17)] = 2.0

    result = compare_annual_onsets(
        rainfall,
        season_start_month=6,
        season_start_day=1,
        season_end_month=7,
        season_end_day=15,
    )

    assert result["baseline"]["years"] == list(range(2001, 2013))
    assert result["recent"]["years"] == list(range(2013, 2026))
    assert result["observed_shift_days"] == 10
    assert result["mann_whitney"]["p_value"] < 0.05
    assert result["mann_whitney"]["rank_biserial_effect"] > 0
    assert [item["threshold_mm"] for item in result["sensitivity"]] == [15, 20, 25]
    assert [item["observed_shift_days"] for item in result["sensitivity"]] == [10, 10, 10]


def test_reports_insufficient_data_instead_of_zero_for_missing_years():
    result = compare_annual_onsets(
        {},
        season_start_month=6,
        season_start_day=1,
        season_end_month=7,
        season_end_day=15,
    )

    assert result["status"] == "insufficient_data"
    assert result["baseline"]["excluded_years"] == list(range(2001, 2013))
    assert result["baseline"]["missing_coverage_years"] == list(range(2001, 2013))


def test_complete_seasons_without_onset_are_not_reported_as_missing_coverage():
    rainfall = {}
    for year in range(2001, 2026):
        start = date(year, 6, 1)
        for offset in range(45):
            rainfall[start + timedelta(days=offset)] = 0.0

    result = compare_annual_onsets(
        rainfall,
        season_start_month=6,
        season_start_day=1,
        season_end_month=7,
        season_end_day=15,
    )

    assert result["baseline"]["missing_coverage_years"] == []
    assert result["baseline"]["no_usable_onset_years"] == list(range(2001, 2013))
