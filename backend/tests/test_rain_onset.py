from datetime import date, datetime, timedelta

from app.services.rain_onset import (
    accumulate_growing_degree_days,
    find_usable_rain_onset,
)


def _rain(start: date, values: list[float | None]) -> dict[date, float | None]:
    return {start + timedelta(days=offset): value for offset, value in enumerate(values)}


def test_finds_first_qualifying_window_and_returns_calendar_date():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [1, 1, 1, 1, 1, 1, 1, 1, 20, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=22))

    assert onset == start + timedelta(days=2)


def test_skips_rain_window_followed_by_a_dry_spell():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4] * 7 + [0] * 14 + [4] * 7 + [0] * 7 + [2] + [0] * 4)

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=39))

    assert onset == start + timedelta(days=19)


def test_rejects_followup_with_a_long_consecutive_dry_spell_even_if_rain_returns():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4] * 7 + [2] + [0] * 10 + [2] + [0] * 14)

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=32))

    assert onset is None


def test_skips_candidate_windows_with_missing_daily_observations():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4, 4, None, 4, 4, 4, 4, 0, 0, 2, 0, 0, 0, 0])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=13))

    assert onset is None


def test_handles_season_crossing_calendar_year():
    start = date(2025, 12, 28)
    rainfall = _rain(start, [4, 4, 4, 4, 4, 0, 0, 2] + [0] * 7 + [2] + [0] * 5)

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=20))

    assert onset == start


def test_returns_none_when_confirmation_period_is_incomplete():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4] * 7)

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=6))

    assert onset is None


def test_gdd_uses_explicit_base_and_does_not_treat_missing_temperature_as_zero():
    temperatures = {
        date(2025, 1, 1): 20.0,
        date(2025, 1, 2): None,
        date(2025, 1, 3): 30.0,
    }

    result = accumulate_growing_degree_days(
        temperatures, date(2025, 1, 1), date(2025, 1, 3), base_temperature_c=10
    )

    assert result.total_degree_days is None
    assert result.valid_days == 2
    assert result.expected_days == 3


def test_gdd_reports_complete_capped_daily_mean_accumulation():
    temperatures = {date(2025, 1, day): 30.0 for day in range(1, 4)}

    result = accumulate_growing_degree_days(
        temperatures,
        date(2025, 1, 1),
        date(2025, 1, 3),
        base_temperature_c=10,
        cap_temperature_c=25,
    )

    assert result.total_degree_days == 45
    assert result.complete
