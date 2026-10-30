"""Deterministic onset detection for a declared usable-rain definition.

This function identifies a date in an observed daily rainfall series. It does
not itself recommend a crop or planting date.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Mapping


def find_usable_rain_onset(
    daily_rain_mm: Mapping[date, float | None],
    season_start: date,
    season_end: date,
    *,
    window_days: int = 7,
    threshold_mm: float = 20.0,
    confirmation_days: int = 7,
    minimum_followup_rain_mm: float = 1.0,
) -> date | None:
    """Return the first qualifying onset date, or ``None`` when unsupported.

    A candidate is the first day of a complete ``window_days`` period whose
    accumulated rainfall reaches ``threshold_mm``, followed by a complete
    ``confirmation_days`` period containing at least one day above
    ``minimum_followup_rain_mm``. Missing, negative, or non-finite daily values
    invalidate that candidate; missing observations are never treated as zero.
    ``season_end`` is inclusive and seasons may cross calendar years.
    """
    if season_end < season_start:
        raise ValueError("season_end must not precede season_start")
    if window_days < 1 or confirmation_days < 1:
        raise ValueError("window_days and confirmation_days must be positive")
    if not math.isfinite(threshold_mm) or threshold_mm < 0:
        raise ValueError("threshold_mm must be finite and non-negative")
    if not math.isfinite(minimum_followup_rain_mm) or minimum_followup_rain_mm < 0:
        raise ValueError("minimum_followup_rain_mm must be finite and non-negative")

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
            followup_has_rain = any(
                float(daily_rain_mm[day]) > minimum_followup_rain_mm
                for day in followup_dates
            )
            if accumulated >= threshold_mm and followup_has_rain:
                return candidate

        candidate += timedelta(days=1)

    return None
