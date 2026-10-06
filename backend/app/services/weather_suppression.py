"""Weather alert suppression engine — the core value-add of Module 4.

Guiding principle (schema doc, line 568, verbatim):

    "The system should avoid simply notifying the farmer about weather without
     determining whether it changes what the farmer should do."

So this engine NEVER emits a bare weather report. The pipeline mirrors the
schema's intended reasoning flow (lines 546-566):

    Weather -> Weather Event -> Farm Location -> Current Crop -> Growth Stage
    -> Current/Upcoming Tasks -> Potential Impact -> Recommended Action
    -> Weather Alert

Concretely:

1. **Detect events** from forecast data against configurable thresholds
   (:mod:`weather_thresholds`). Each detected event records which threshold it
   crossed and the facts that crossed it (provenance).
2. **Decide, per event, whether it changes a required action** by inspecting
   the farm-state slice (crop, stage, current/upcoming tasks). If nothing the
   farmer is about to do changes, the event is **suppressed** — no alert.
3. **Emit an alert** only for events that survive, with a concrete
   ``recommended_action`` (the thing the farmer should now do differently).

The engine is pure: it takes a weather payload + a
:class:`~app.services.mock_farm_state.FarmStateSlice` and returns plain result
objects. Persisting events/alerts to ``weather_events`` / ``weather_alerts`` is
the route layer's job, not the engine's.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.mock_farm_state import FarmStateSlice, TaskRef
from app.services.weather_thresholds import Threshold, get_thresholds

# Severity ordering helper for sorting/comparison.
_SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass
class DetectedEvent:
    """A weather event detected from the forecast, before suppression.

    Maps to a ``weather_events`` row: ``event_type``/``severity``/``start_time``
    /``end_time`` become columns; everything else (facts, threshold provenance)
    goes into the ``data`` JSON.
    """

    event_type: str
    severity: str
    description: str
    start_date: str | None
    end_date: str | None
    threshold: Threshold
    facts: dict[str, Any] = field(default_factory=dict)

    def to_event_data(self) -> dict[str, Any]:
        """Rich payload for the ``weather_events.data`` JSON column."""
        return {
            "facts": self.facts,
            "threshold": self.threshold.as_dict(),
            "detected_window": {"start": self.start_date, "end": self.end_date},
        }


@dataclass
class AlertDecision:
    """The engine's decision about one detected event.

    When ``emitted`` is True an alert should be created; when False the event
    was suppressed and ``suppression_reason`` explains why (kept for
    transparency/debugging, never shown to the farmer as a bare report).
    """

    event: DetectedEvent
    emitted: bool
    suppression_reason: str | None = None
    title: str | None = None
    message: str | None = None
    recommended_action: str | None = None
    triggering_tasks: list[TaskRef] = field(default_factory=list)


@dataclass
class SuppressionResult:
    """Full engine output: detected events + per-event decisions + alerts."""

    detected_events: list[DetectedEvent]
    decisions: list[AlertDecision]

    @property
    def alerts(self) -> list[AlertDecision]:
        return [d for d in self.decisions if d.emitted]

    @property
    def suppressed(self) -> list[AlertDecision]:
        return [d for d in self.decisions if not d.emitted]


# ── Event detection ────────────────────────────────────────────────────────────
def detect_events(
    weather: dict[str, Any],
    thresholds: dict[str, Threshold],
) -> list[DetectedEvent]:
    """Detect weather events from the forecast block against ``thresholds``.

    Only the forecast (future) drives events — NASA POWER observed data is
    context, not an action trigger. If the forecast is unavailable, no events
    are detected (graceful degradation).
    """
    forecast = weather.get("forecast") or {}
    if forecast.get("state") != "available":
        return []
    days = ((forecast.get("data") or {}).get("daily")) or []

    events: list[DetectedEvent] = []

    # Heavy rain: any day whose precipitation crosses the heavy-rain threshold.
    heavy_rain = thresholds["heavy_rain_mm"]
    rain_days = [
        d for d in days
        if _num(d.get("precipitation_mm")) is not None
        and _num(d.get("precipitation_mm")) >= heavy_rain.value
    ]
    if rain_days:
        peak = max(rain_days, key=lambda d: _num(d.get("precipitation_mm")) or 0.0)
        peak_mm = _num(peak.get("precipitation_mm")) or 0.0
        events.append(
            DetectedEvent(
                event_type="heavy_rain",
                severity="high" if peak_mm >= heavy_rain.value * 1.5 else "medium",
                description=(
                    f"Heavy rain forecast: up to {peak_mm:.0f} mm on {peak['date']} "
                    f"(threshold {heavy_rain.value:.0f} {heavy_rain.unit})."
                ),
                start_date=rain_days[0]["date"],
                end_date=rain_days[-1]["date"],
                threshold=heavy_rain,
                facts={
                    "peak_precipitation_mm": round(peak_mm, 1),
                    "peak_date": peak["date"],
                    "rain_days": [
                        {"date": d["date"], "precipitation_mm": _num(d.get("precipitation_mm"))}
                        for d in rain_days
                    ],
                },
            )
        )

    # Heat stress: any day whose max temperature crosses the heat threshold.
    heat = thresholds["heat_stress_max_c"]
    hot_days = [
        d for d in days
        if _num(d.get("temperature_max_c")) is not None
        and _num(d.get("temperature_max_c")) >= heat.value
    ]
    if hot_days:
        peak = max(hot_days, key=lambda d: _num(d.get("temperature_max_c")) or 0.0)
        peak_c = _num(peak.get("temperature_max_c")) or 0.0
        events.append(
            DetectedEvent(
                event_type="heat_stress",
                severity="high" if peak_c >= heat.value + 3 else "medium",
                description=(
                    f"High temperatures forecast: up to {peak_c:.0f}degC on {peak['date']} "
                    f"(threshold {heat.value:.0f} {heat.unit})."
                ),
                start_date=hot_days[0]["date"],
                end_date=hot_days[-1]["date"],
                threshold=heat,
                facts={"peak_temperature_c": round(peak_c, 1), "peak_date": peak["date"]},
            )
        )

    # High wind: any day whose max wind crosses the wind threshold.
    wind = thresholds["high_wind_kmh"]
    windy_days = [
        d for d in days
        if _num(d.get("wind_speed_max_kmh")) is not None
        and _num(d.get("wind_speed_max_kmh")) >= wind.value
    ]
    if windy_days:
        peak = max(windy_days, key=lambda d: _num(d.get("wind_speed_max_kmh")) or 0.0)
        peak_kmh = _num(peak.get("wind_speed_max_kmh")) or 0.0
        events.append(
            DetectedEvent(
                event_type="high_wind",
                severity="high" if peak_kmh >= wind.value + 20 else "medium",
                description=(
                    f"Strong winds forecast: up to {peak_kmh:.0f} km/h on {peak['date']} "
                    f"(threshold {wind.value:.0f} {wind.unit})."
                ),
                start_date=windy_days[0]["date"],
                end_date=windy_days[-1]["date"],
                threshold=wind,
                facts={"peak_wind_kmh": round(peak_kmh, 1), "peak_date": peak["date"]},
            )
        )

    return events


# ── Suppression: does the event change a required action? ──────────────────────
#
# Each event type maps to the task categories it would change. An event is only
# promoted to an alert if the farm has an active task in one of those categories
# (or, for some events, a crop/stage-level standing action). Otherwise it is
# suppressed: the weather is real but changes nothing the farmer must do.
_EVENT_IMPACT = {
    "heavy_rain": {"irrigation", "spraying", "fertilizing"},
    "heat_stress": {"irrigation", "transplanting"},
    "high_wind": {"spraying", "harvest"},
}


def _decide(event: DetectedEvent, farm: FarmStateSlice) -> AlertDecision:
    """Decide whether ``event`` changes a required action for ``farm``."""
    impacted_categories = _EVENT_IMPACT.get(event.event_type, set())
    triggering = farm.tasks_in(impacted_categories)

    if not triggering:
        return AlertDecision(
            event=event,
            emitted=False,
            suppression_reason=(
                f"{event.event_type} detected but no active "
                f"{sorted(impacted_categories)} task for {farm.crop_name} "
                f"at {farm.growth_stage} stage; nothing the farmer must change."
            ),
        )

    title, message, action = _compose_advice(event, farm, triggering)
    return AlertDecision(
        event=event,
        emitted=True,
        title=title,
        message=message,
        recommended_action=action,
        triggering_tasks=triggering,
    )


def _compose_advice(
    event: DetectedEvent,
    farm: FarmStateSlice,
    triggering: list[TaskRef],
) -> tuple[str, str, str]:
    """Produce (title, message, recommended_action) for an emitted alert."""
    task_titles = ", ".join(t.title for t in triggering)

    if event.event_type == "heavy_rain":
        irrigation = [t for t in triggering if t.category == "irrigation"]
        if irrigation:
            return (
                "Heavy rain coming - skip irrigation",
                (
                    f"{event.description} Your {farm.crop_name} field at "
                    f"{farm.location_name} has irrigation scheduled ({task_titles}). "
                    f"The forecast rain should meet the crop's water needs."
                ),
                "Skip the scheduled irrigation and let the rain water the field; "
                "check soil moisture after the rain before resuming.",
            )
        return (
            "Heavy rain coming - adjust field work",
            f"{event.description} This affects scheduled work: {task_titles}.",
            f"Postpone {task_titles.lower()} until after the rain passes.",
        )

    if event.event_type == "heat_stress":
        return (
            "High heat coming - protect the crop",
            (
                f"{event.description} Your {farm.crop_name} at {farm.growth_stage} "
                f"stage is sensitive; this affects: {task_titles}."
            ),
            "Irrigate in the early morning or evening to reduce heat stress, and "
            "avoid working the crop during peak afternoon heat.",
        )

    if event.event_type == "high_wind":
        return (
            "Strong winds coming - hold off",
            f"{event.description} This affects scheduled work: {task_titles}.",
            f"Postpone {task_titles.lower()} until winds drop, to avoid spray "
            "drift and crop damage.",
        )

    # Fallback (should not hit for known event types).
    return (
        f"Weather alert: {event.event_type}",
        event.description,
        f"Review scheduled work: {task_titles}.",
    )


def run_suppression(
    weather: dict[str, Any],
    farm: FarmStateSlice,
    threshold_overrides: dict[str, float] | None = None,
) -> SuppressionResult:
    """Full pipeline: detect events, then emit/suppress per farm state.

    This is the single entry point the route layer calls.
    """
    thresholds = get_thresholds(threshold_overrides)
    events = detect_events(weather, thresholds)
    decisions = [_decide(event, farm) for event in events]
    # Most severe emitted alerts first.
    decisions.sort(
        key=lambda d: (d.emitted, _SEVERITY_RANK.get(d.event.severity, 0)),
        reverse=True,
    )
    return SuppressionResult(detected_events=events, decisions=decisions)


def _num(value: Any) -> float | None:
    """Coerce to float or None (missing readings stay None, never 0)."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
