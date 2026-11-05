"""Documented units/scale seams; decoded values still require product QA flags."""
import math


def normalize_precipitation(value: float, *, units: str, fill_value: float | None = None,
                            interval_hours: float | None = None) -> float | None:
    if units not in ('mm/day', 'mm', 'mm/hr', 'mm/h'):
        raise ValueError('Unsupported precipitation unit')
    if not math.isfinite(value) or value == fill_value or value < 0:
        return None
    if units in ('mm/hr', 'mm/h'):
        if interval_hours is None or not math.isfinite(interval_hours) or not 0 < interval_hours <= 24:
            raise ValueError('Rate unit needs a bounded integration interval')
        return value * interval_hours
    return value


def landsat_ndvi(red_dn: float, nir_dn: float, *, quality_ok: bool) -> float | None:
    if not quality_ok or any(not math.isfinite(v) or not 1 <= v <= 65455 for v in (red_dn,nir_dn)):
        return None
    red, nir = red_dn*0.0000275-0.2, nir_dn*0.0000275-0.2
    if red < 0 or nir < 0 or red+nir <= 1e-8:
        return None
    return (nir-red)/(nir+red)
