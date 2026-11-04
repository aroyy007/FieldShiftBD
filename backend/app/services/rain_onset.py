"""Compatibility imports; canonical pure science lives in src.compute.agro."""

from src.compute.agro import (
    GrowingDegreeDayResult,
    accumulate_growing_degree_days,
    find_usable_rain_onset,
)

__all__ = ["GrowingDegreeDayResult", "accumulate_growing_degree_days", "find_usable_rain_onset"]
