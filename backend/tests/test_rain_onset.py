from datetime import date, timedelta

from app.services.rain_onset import find_usable_rain_onset


def _rain(start: date, values: list[float | None]) -> dict[date, float | None]:
    return {start + timedelta(days=offset): value for offset, value in enumerate(values)}


def test_finds_first_qualifying_window_and_returns_calendar_date():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [1, 1, 1, 1, 1, 1, 1, 1, 20, 0, 0, 2, 0, 0, 0, 0])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=15))

    assert onset == start + timedelta(days=2)


def test_skips_rain_window_followed_by_a_dry_spell():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4] * 7 + [0] * 14 + [4] * 7 + [0] * 7 + [2])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=35))

    assert onset == start + timedelta(days=19)


def test_skips_candidate_windows_with_missing_daily_observations():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4, 4, None, 4, 4, 4, 4, 0, 0, 2, 0, 0, 0, 0])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=13))

    assert onset is None


def test_handles_season_crossing_calendar_year():
    start = date(2025, 12, 28)
    rainfall = _rain(start, [4, 4, 4, 4, 4, 0, 0, 2, 0, 0, 0, 0, 0, 0])

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=13))

    assert onset == start


def test_returns_none_when_confirmation_period_is_incomplete():
    start = date(2025, 6, 1)
    rainfall = _rain(start, [4] * 7)

    onset = find_usable_rain_onset(rainfall, start, start + timedelta(days=6))

    assert onset is None
