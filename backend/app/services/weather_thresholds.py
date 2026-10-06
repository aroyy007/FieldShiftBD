"""Weather alert thresholds with explicit provenance.

A core M4 requirement: thresholds are *configurable and attributable*, never
magic numbers buried in logic. Each threshold records its value, unit, and a
short ``source`` note so an agronomist can review and tune it, and so an alert
can cite *why* it fired. The team schema has no column for this provenance, so
it lives here (M4-internal) and is surfaced inside the weather event's ``data``
JSON; promoting it to a shared table is a Milestone-0 ask (contract doc).

These defaults are first-pass demo values for Bangladesh smallholder context,
not validated agronomy. Treat them as placeholders pending expert review.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Threshold:
    """A single tunable threshold with its unit and provenance note."""

    key: str
    value: float
    unit: str
    source: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
        }


# Default threshold set. Keyed for lookup; each carries its own provenance.
DEFAULT_THRESHOLDS: dict[str, Threshold] = {
    "heavy_rain_mm": Threshold(
        key="heavy_rain_mm",
        value=40.0,
        unit="mm/day",
        source=(
            "Demo placeholder: daily rainfall above this is treated as heavy "
            "enough to make same-day irrigation redundant/harmful. Pending "
            "agronomist review."
        ),
    ),
    "heat_stress_max_c": Threshold(
        key="heat_stress_max_c",
        value=36.0,
        unit="degC",
        source="Demo placeholder: daily max above this flags heat stress risk.",
    ),
    "high_wind_kmh": Threshold(
        key="high_wind_kmh",
        value=45.0,
        unit="km/h",
        source=(
            "Demo placeholder: max wind above this flags spraying as unsafe "
            "(drift) and lodging risk."
        ),
    ),
    "rain_probability_percent": Threshold(
        key="rain_probability_percent",
        value=70.0,
        unit="percent",
        source=(
            "Demo placeholder: forecast rain probability above this is treated "
            "as likely enough to act on."
        ),
    ),
}


def get_thresholds(overrides: dict[str, float] | None = None) -> dict[str, Threshold]:
    """Return the active threshold set, applying optional value overrides.

    ``overrides`` maps a threshold key to a new numeric value; unit and source
    are preserved (the source gets an ``(overridden)`` suffix for traceability).
    This is the configuration seam — callers/config can tune values without
    touching rule logic.
    """
    if not overrides:
        return dict(DEFAULT_THRESHOLDS)

    merged: dict[str, Threshold] = {}
    for key, base in DEFAULT_THRESHOLDS.items():
        if key in overrides:
            merged[key] = Threshold(
                key=base.key,
                value=float(overrides[key]),
                unit=base.unit,
                source=f"{base.source} (overridden)",
            )
        else:
            merged[key] = base
    return merged