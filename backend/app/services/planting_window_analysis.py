"""Annual usable-rain onset comparisons with explicit evidence coverage."""

from __future__ import annotations

import math
from datetime import date, timedelta
from statistics import median
from typing import Mapping

from app.services.rain_onset import find_usable_rain_onset

BASELINE_YEARS = tuple(range(2001, 2013))
RECENT_YEARS = tuple(range(2013, 2026))
SENSITIVITY_THRESHOLDS_MM = (15.0, 20.0, 25.0)


def _season_dates(year: int, start_month: int, start_day: int,
                  end_month: int, end_day: int) -> tuple[date, date]:
    start = date(year, start_month, start_day)
    end_year = year + (1 if (end_month, end_day) < (start_month, start_day) else 0)
    # Calendar days such as Feb 29 are not silently fabricated for every year.
    end = date(end_year, end_month, end_day)
    return start, end


def _mann_whitney(left: list[int], right: list[int]) -> dict[str, float | int | None]:
    """Two-sided asymptotic Mann–Whitney U with tie correction."""
    n1, n2 = len(left), len(right)
    if not n1 or not n2:
        return {"u_statistic": 0.0, "p_value": None, "rank_biserial_effect": None}
    combined = [(value, 0) for value in left] + [(value, 1) for value in right]
    combined.sort(key=lambda item: item[0])
    rank_sums = [0.0, 0.0]
    tie_sizes: list[int] = []
    index = 0
    while index < len(combined):
        end = index + 1
        while end < len(combined) and combined[end][0] == combined[index][0]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        for _, group in combined[index:end]:
            rank_sums[group] += average_rank
        tie_sizes.append(end - index)
        index = end
    u1 = rank_sums[0] - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u_min = min(u1, u2)
    n = n1 + n2
    tie_term = sum(size**3 - size for size in tie_sizes)
    variance = n1 * n2 / 12 * ((n + 1) - tie_term / (n * (n - 1))) if n > 1 else 0
    if variance <= 0:
        p_value = 1.0
    else:
        z = max(0.0, abs(u1 - n1 * n2 / 2) - 0.5) / math.sqrt(variance)
        p_value = math.erfc(z / math.sqrt(2))
    # Positive means recent onsets tend to occur later than the baseline.
    effect = (u2 / (n1 * n2) * 2) - 1
    return {"u_statistic": round(u_min, 3), "p_value": round(p_value, 6),
            "rank_biserial_effect": round(effect, 4)}


def _period(years: tuple[int, ...], onset_by_year: Mapping[int, int | None],
            coverage: Mapping[int, bool]) -> dict:
    included = [year for year in years if coverage.get(year) and onset_by_year.get(year) is not None]
    return {
        "years": included,
        "onset_day_offsets": [onset_by_year[year] for year in included],
        "median_onset_day": median(onset_by_year[year] for year in included) if included else None,
        "excluded_years": [year for year in years if year not in included],
        "missing_coverage_years": [year for year in years if not coverage.get(year, False)],
        "no_usable_onset_years": [year for year in years if coverage.get(year, False) and onset_by_year.get(year) is None],
        "sample_size": len(included),
    }


def compare_annual_onsets(
    daily_rain_mm: Mapping[date, float | None], *,
    season_start_month: int,
    season_start_day: int,
    season_end_month: int,
    season_end_day: int,
    years: tuple[int, ...] = tuple(range(2001, 2026)),
    thresholds_mm: tuple[float, ...] = SENSITIVITY_THRESHOLDS_MM,
    minimum_period_samples: int = 8,
) -> dict:
    """Compare annual onset offsets for 2001–12 and 2013–25 by default.

    A year enters the test only when every date in its declared season is
    observed. This avoids treating data gaps or an undetected onset as day 0.
    Threshold sensitivity is an alternate operational definition, not a
    confidence interval.
    """
    if not all(1 <= month <= 12 for month in (season_start_month, season_end_month)):
        raise ValueError("season months must be between 1 and 12")
    if not all(1 <= day <= 31 for day in (season_start_day, season_end_day)):
        raise ValueError("season days must be between 1 and 31")
    if any(threshold not in SENSITIVITY_THRESHOLDS_MM for threshold in thresholds_mm):
        raise ValueError("thresholds_mm must use the declared 15, 20, and 25 mm sensitivity values")

    present_years = set(years)
    baseline_years = tuple(year for year in BASELINE_YEARS if year in present_years)
    recent_years = tuple(year for year in RECENT_YEARS if year in present_years)
    season_ranges: dict[int, tuple[date, date]] = {}
    coverage: dict[int, bool] = {}
    for year in years:
        try:
            start, end = _season_dates(year, season_start_month, season_start_day,
                                      season_end_month, season_end_day)
        except ValueError:
            coverage[year] = False
            continue
        season_ranges[year] = (start, end)
        coverage[year] = all(
            day in daily_rain_mm and daily_rain_mm[day] is not None
            and math.isfinite(float(daily_rain_mm[day])) and float(daily_rain_mm[day]) >= 0
            for day in (start + timedelta(days=offset)
                        for offset in range((end - start).days + 1))
        )

    sensitivity = []
    onset_maps: dict[float, dict[int, int | None]] = {}
    for threshold in thresholds_mm:
        onset_by_year: dict[int, int | None] = {}
        for year, (start, end) in season_ranges.items():
            onset = find_usable_rain_onset(
                daily_rain_mm, start, end, window_days=7,
                threshold_mm=threshold, confirmation_days=14,
                dry_day_threshold_mm=1.0, max_consecutive_dry_days=7,
            ) if coverage[year] else None
            onset_by_year[year] = (onset - start).days if onset else None
        onset_maps[threshold] = onset_by_year
        baseline = _period(baseline_years, onset_by_year, coverage)
        recent = _period(recent_years, onset_by_year, coverage)
        enough = (baseline["sample_size"] >= minimum_period_samples
                  and recent["sample_size"] >= minimum_period_samples)
        shift = (round(recent["median_onset_day"] - baseline["median_onset_day"], 2)
                 if enough else None)
        sensitivity.append({
            "threshold_mm": threshold,
            "status": "available" if enough else "insufficient_data",
            "baseline_median_onset_day": baseline["median_onset_day"],
            "recent_median_onset_day": recent["median_onset_day"],
            "observed_shift_days": shift,
            "baseline_sample_size": baseline["sample_size"],
            "recent_sample_size": recent["sample_size"],
        })

    primary = onset_maps.get(20.0)
    if primary is None:
        primary = onset_maps.get(thresholds_mm[0]) if thresholds_mm else {}
    baseline = _period(baseline_years, primary or {}, coverage)
    recent = _period(recent_years, primary or {}, coverage)
    enough = (baseline["sample_size"] >= minimum_period_samples
              and recent["sample_size"] >= minimum_period_samples)
    shift = (round(recent["median_onset_day"] - baseline["median_onset_day"], 2)
             if enough else None)
    return {
        "status": "available" if enough else "insufficient_data",
        "definition": {
            "window_days": 7, "threshold_mm": 20,
            "confirmation_days": 14, "dry_day_threshold_mm": 1,
            "max_consecutive_dry_days": 7,
            "season_start": f"{season_start_month:02d}-{season_start_day:02d}",
            "season_end": f"{season_end_month:02d}-{season_end_day:02d}",
        },
        "baseline_period": f"{min(baseline_years)}-{max(baseline_years)}" if baseline_years else None,
        "recent_period": f"{min(recent_years)}-{max(recent_years)}" if recent_years else None,
        "baseline": baseline,
        "recent": recent,
        "observed_shift_days": shift,
        "mann_whitney": _mann_whitney(baseline["onset_day_offsets"], recent["onset_day_offsets"]) if enough else {
            "u_statistic": None, "p_value": None, "rank_biserial_effect": None
        },
        "sensitivity": sensitivity,
        "limitation": "Historical area-level weather comparison; not a field measurement or a crop-specific planting recommendation.",
    }
