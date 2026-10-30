"""Deterministic onset detection for a declared usable-rain definition.

This function identifies a date in an observed daily rainfall series. It does
not itself recommend a crop or planting date.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping


@dataclass(frozen=True)
class GrowingDegreeDayResult:
    total_degree_days: float | None
    expected_days: int
    valid_days: int
    method: str
    base_temperature_c: float
    cap_temperature_c: float | None

    @property
    def complete(self) -> bool:
        return self.valid_days == self.expected_days and self.total_degree_days is not None


def accumulate_growing_degree_days(
    daily_mean_temperature_c: Mapping[date, float | None],
    start: date,
    end: date,
    *,
    base_temperature_c: float,
    cap_temperature_c: float | None = None,
) -> GrowingDegreeDayResult:
    """Accumulate daily-mean GDD; missing days make the total unavailable."""
    if end < start:
        raise ValueError("end must not precede start")
    if not math.isfinite(base_temperature_c):
        raise ValueError("base_temperature_c must be finite")
    if cap_temperature_c is not None and (
        not math.isfinite(cap_temperature_c) or cap_temperature_c < base_temperature_c
    ):
        raise ValueError("cap_temperature_c must be finite and at least the base")

    expected_days = (end - start).days + 1
    values: list[float] = []
    for offset in range(expected_days):
        day = start + timedelta(days=offset)
        value = daily_mean_temperature_c.get(day)
        if value is None or not math.isfinite(float(value)):
            continue
        temperature = float(value)
        if cap_temperature_c is not None:
            temperature = min(temperature, cap_temperature_c)
        values.append(max(0.0, temperature - base_temperature_c))

    return GrowingDegreeDayResult(
        total_degree_days=(round(sum(values), 2) if len(values) == expected_days else None),
        expected_days=expected_days,
        valid_days=len(values),
        method="daily_mean_max_zero_v1",
        base_temperature_c=base_temperature_c,
        cap_temperature_c=cap_temperature_c,
    )


def find_usable_rain_onset(
    daily_rain_mm: Mapping[date, float | None],
    season_start: date,
    season_end: date,
    *,
    window_days: int = 7,
    threshold_mm: float = 20.0,
    confirmation_days: int = 14,
    dry_day_threshold_mm: float = 1.0,
    max_consecutive_dry_days: int = 7,
) -> date | None:
    """Return the first qualifying onset date, or ``None`` when unsupported.

    A candidate is the first day of a complete ``window_days`` period whose
    accumulated rainfall reaches ``threshold_mm``, followed by a complete
    ``confirmation_days`` period with no run longer than
    ``max_consecutive_dry_days`` where daily rain is at or below
    ``dry_day_threshold_mm``. Missing, negative, or non-finite daily values
    invalidate that candidate; missing observations are never treated as zero.
    ``season_end`` is inclusive and seasons may cross calendar years.
    """
    if season_end < season_start:
        raise ValueError("season_end must not precede season_start")
    if window_days < 1 or confirmation_days < 1:
        raise ValueError("window_days and confirmation_days must be positive")
    if not math.isfinite(threshold_mm) or threshold_mm < 0:
        raise ValueError("threshold_mm must be finite and non-negative")
    if not math.isfinite(dry_day_threshold_mm) or dry_day_threshold_mm < 0:
        raise ValueError("dry_day_threshold_mm must be finite and non-negative")
    if max_consecutive_dry_days < 0:
        raise ValueError("max_consecutive_dry_days must be non-negative")

    required_days = window_days + confirmation_days
    final_candidate = season_end - timedelta(days=required_days - 1)
    candidate = season_start

    while candidate <= final_candidate:
        accumulation_dates = [candidate + timedelta(days=offset) for offset in range(window_days)]
        followup_start = candidate + timedelta(days=window_days)
        followup_dates = [
            followup_start + timedelta(days=offset) for offset in range(confirmation_days)
        ]
        values = [daily_rain_mm.get(day) for day in accumulation_dates + followup_dates]

        if all(
            value is not None and math.isfinite(float(value)) and float(value) >= 0
            for value in values
        ):
            accumulated = sum(float(daily_rain_mm[day]) for day in accumulation_dates)
            longest_dry_spell = 0
            current_dry_spell = 0
            for day in followup_dates:
                if float(daily_rain_mm[day]) <= dry_day_threshold_mm:
                    current_dry_spell += 1
                    longest_dry_spell = max(longest_dry_spell, current_dry_spell)
                else:
                    current_dry_spell = 0
            if accumulated >= threshold_mm and longest_dry_spell <= max_consecutive_dry_days:
                return candidate

        candidate += timedelta(days=1)

    return None
