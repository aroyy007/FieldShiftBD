"""Module 4 (Weather Intelligence & Alerts) HTTP routes.

All paths live under ``/weather`` (per-module router convention,
``backend/guide.md``). The endpoints wire together the M4 service layer:

* provider adapters      (:mod:`app.services.weather_providers`)
* mock M3 farm state     (:mod:`app.services.mock_farm_state`)
* suppression engine     (:mod:`app.services.weather_suppression`)

Core product rule enforced here: an *assessment* returns farmer-facing ALERTS,
not a weather report. The raw forecast is only exposed on an explicitly-named
debug endpoint, never as the primary farmer output.

This router is deliberately read-only for now (no DB writes). Persisting
emitted alerts to ``weather_alerts`` is a follow-up once a live Postgres +
migration are in place; the result objects already carry everything needed.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import (
    ProviderStatusOut,
    SuppressedEventOut,
    WeatherAlertOut,
    WeatherAssessmentOut,
)
from app.services import mock_farm_state
from app.services.weather_providers import WeatherProviderError, fetch_weather
from app.services.weather_suppression import SuppressionResult, run_suppression

router = APIRouter(prefix="/weather", tags=["Weather (M4)"])


def _provider_statuses(weather: dict[str, Any]) -> list[ProviderStatusOut]:
    statuses: list[ProviderStatusOut] = []
    for provider, block in (("open-meteo", weather.get("forecast")),
                            ("nasa-power", weather.get("nasa_power"))):
        block = block or {}
        statuses.append(
            ProviderStatusOut(
                provider=provider,
                state=block.get("state", "unavailable"),
                reason=block.get("reason"),
            )
        )
    return statuses


def _build_assessment(
    farm: mock_farm_state.FarmStateSlice,
    weather: dict[str, Any],
    result: SuppressionResult,
) -> WeatherAssessmentOut:
    alerts = [
        WeatherAlertOut(
            title=d.title,
            message=d.message,
            recommended_action=d.recommended_action,
            severity=d.event.severity,
            event_type=d.event.event_type,
            triggering_task_titles=[t.title for t in d.triggering_tasks],
        )
        for d in result.alerts
    ]
    suppressed = [
        SuppressedEventOut(
            event_type=d.event.event_type,
            severity=d.event.severity,
            suppression_reason=d.suppression_reason or "",
        )
        for d in result.suppressed
    ]
    coords = weather.get("coordinates") or {
        "latitude": farm.latitude,
        "longitude": farm.longitude,
    }
    return WeatherAssessmentOut(
        farmland_id=str(farm.farmland_id),
        crop_name=farm.crop_name,
        growth_stage=farm.growth_stage,
        location_name=farm.location_name,
        coordinates=coords,
        assessed_at=date.today(),
        providers=_provider_statuses(weather),
        alerts=alerts,
        suppressed_events=suppressed,
        detected_event_count=len(result.detected_events),
    )


@router.get("/assessment/{farmland_id}", response_model=WeatherAssessmentOut)
def get_weather_assessment(farmland_id: uuid.UUID) -> WeatherAssessmentOut:
    """Assess weather for a farmland and return ALERTS (never a bare report).

    Fetches both providers for the farmland's location, runs the suppression
    engine against the (mock M3) farm state, and returns only alerts that
    change what the farmer should do, plus a transparency list of what was
    suppressed.
    """
    farm = mock_farm_state.get_farm_state_slice(farmland_id)
    if farm is None:
        raise HTTPException(status_code=404, detail="farmland not found in farm state")

    weather = fetch_weather(farm.latitude, farm.longitude)
    result = run_suppression(weather, farm)
    return _build_assessment(farm, weather, result)


@router.get("/assessment/{farmland_id}/demo", response_model=WeatherAssessmentOut)
def get_weather_assessment_demo(
    farmland_id: uuid.UUID,
    rain_mm: float = Query(
        48.0, description="Mock forecast rainfall (mm) for tomorrow, to drive the demo."
    ),
    with_irrigation_task: bool = Query(
        True,
        description=(
            "Golden Farm variant: True keeps the irrigation task (alert fires); "
            "False removes it (same weather is suppressed)."
        ),
    ),
) -> WeatherAssessmentOut:
    """Offline suppression demo using mock weather (no upstream calls).

    Demonstrates the core principle deterministically: identical weather yields
    an alert when an irrigation task exists and is suppressed when it does not.
    Works without a network or running providers.
    """
    if farmland_id != mock_farm_state.GOLDEN_FARMLAND_ID:
        raise HTTPException(
            status_code=404,
            detail="demo only available for the Golden Farm farmland id",
        )
    farm = (
        mock_farm_state.golden_farm_with_irrigation()
        if with_irrigation_task
        else mock_farm_state.golden_farm_without_irrigation()
    )
    mock_weather = {
        "coordinates": {"latitude": farm.latitude, "longitude": farm.longitude},
        "forecast": {
            "state": "available",
            "data": {
                "daily": [
                    {
                        "date": date.today().isoformat(),
                        "precipitation_mm": rain_mm,
                        "temperature_max_c": 31.0,
                        "temperature_min_c": 24.0,
                        "wind_speed_max_kmh": 12.0,
                        "precipitation_probability_percent": 90,
                    }
                ]
            },
        },
        "nasa_power": {"state": "unavailable", "reason": "demo_mode"},
    }
    result = run_suppression(mock_weather, farm)
    return _build_assessment(farm, mock_weather, result)


@router.get("/raw/{farmland_id}")
def get_raw_weather(farmland_id: uuid.UUID) -> dict[str, Any]:
    """Debug-only raw provider payload (NOT a farmer-facing endpoint).

    Exposed for development/inspection. The farmer-facing surface is
    ``/assessment`` which only returns actionable alerts.
    """
    farm = mock_farm_state.get_farm_state_slice(farmland_id)
    if farm is None:
        raise HTTPException(status_code=404, detail="farmland not found in farm state")
    try:
        return fetch_weather(farm.latitude, farm.longitude)
    except WeatherProviderError as exc:
        raise HTTPException(status_code=502, detail=f"weather providers failed: {exc}") from exc
