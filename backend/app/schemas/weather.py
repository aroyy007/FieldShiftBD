"""Pydantic response schemas for Module 4 weather endpoints.

These are the API contract (what the frontend alerts screen consumes), kept
separate from the ORM models and the engine's internal dataclasses. Following
the schema doc's principle (section 14): not every internal type needs a table
or an identical wire shape.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ThresholdOut(BaseModel):
    """A threshold with its provenance, echoed so an alert can cite why it fired."""

    key: str
    value: float
    unit: str
    source: str


class WeatherEventOut(BaseModel):
    """A detected weather event (pre- or post-suppression)."""

    event_type: str
    severity: str
    description: str
    start_date: str | None = None
    end_date: str | None = None
    threshold: ThresholdOut
    facts: dict[str, Any] = Field(default_factory=dict)


class WeatherAlertOut(BaseModel):
    """A farmer-facing alert — only produced when weather changes a required action."""

    title: str
    message: str
    recommended_action: str
    severity: str
    event_type: str
    triggering_task_titles: list[str] = Field(default_factory=list)


class SuppressedEventOut(BaseModel):
    """An event that was detected but deliberately NOT alerted, with the reason.

    Surfaced for transparency/debugging only; never shown to the farmer as a
    bare weather report.
    """

    event_type: str
    severity: str
    suppression_reason: str


class ProviderStatusOut(BaseModel):
    """Availability of one upstream provider (graceful-degradation signal)."""

    provider: str
    state: str
    reason: str | None = None


class WeatherAssessmentOut(BaseModel):
    """Top-level response for an assessment: alerts + what was suppressed + context."""

    farmland_id: str
    crop_name: str
    growth_stage: str
    location_name: str
    coordinates: dict[str, float]
    assessed_at: date
    providers: list[ProviderStatusOut]
    alerts: list[WeatherAlertOut]
    suppressed_events: list[SuppressedEventOut]
    detected_event_count: int
