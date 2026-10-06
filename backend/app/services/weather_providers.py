"""Weather provider adapters for Module 4.

Two independent upstreams, queried in parallel and each tolerant of failure so
one provider being down never blocks the other:

* **Open-Meteo** — 7-day point forecast (what *will* happen).
* **NASA POWER** — daily observed point data at ~50 km area-scale, lagging ~5
  days (what *did* happen, for context/baselines). NOT field-level.

These are pure functions: they fetch and normalize, and never touch the
database or the farm state. The suppression engine consumes their output.

Ported from the earlier prototype (`fieldshift-bd/api/server.py`), with the
prototype's web-framework glue removed:

* ``ApiError``      -> :class:`WeatherProviderError` (local, framework-free)
* ``UPSTREAM_POOL`` -> a module-level :class:`ThreadPoolExecutor`
* ``now_iso()``     -> :func:`_now_iso`

No secrets or API keys are involved; both providers are open endpoints. A
descriptive, honest User-Agent is sent so upstreams can identify the caller.
"""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────
_USER_AGENT = "FieldShiftBD/1.0 (local advisory tool)"
_HTTP_TIMEOUT_SECONDS = 9.0
_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
_NASA_SENTINEL = -999.0  # POWER's fill value for missing observations
_NASA_LAG_DAYS = 5       # POWER observations trail ~5 days behind today
_NASA_WINDOW_DAYS = 29   # 30-day window inclusive of the end day
_FORECAST_DAYS = 7
_TIMEZONE = "Asia/Dhaka"

# Small pool so the two upstream calls overlap instead of running serially.
_UPSTREAM_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="wx")


class WeatherProviderError(RuntimeError):
    """Raised when an upstream weather provider cannot return usable data.

    Carries a short machine-readable ``code`` (e.g. ``"nasa_power_no_data"``,
    ``"http_error"``, ``"timeout"``) so callers can branch without string
    matching, while the message stays human-readable for logs.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _now_iso() -> str:
    """Current UTC time as an ISO-8601 string (replaces prototype ``now_iso``)."""
    return datetime.now(timezone.utc).isoformat()


def _http_json(url: str) -> dict[str, Any]:
    """GET ``url`` and parse JSON, raising :class:`WeatherProviderError`.

    Framework-free: uses urllib so the services layer has no web dependency.
    """
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise WeatherProviderError(
                    "http_error",
                    f"upstream returned HTTP {response.status} for {url}",
                )
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise WeatherProviderError("http_error", f"HTTP {exc.code} from upstream") from exc
    except urllib.error.URLError as exc:
        raise WeatherProviderError("network_error", f"could not reach upstream: {exc.reason}") from exc
    except TimeoutError as exc:
        raise WeatherProviderError("timeout", "upstream timed out") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise WeatherProviderError("bad_payload", "upstream returned invalid JSON") from exc


def _validate_coords(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise WeatherProviderError(
            "bad_coordinates",
            f"coordinates out of range: lat={lat}, lon={lon}",
        )


def fetch_open_meteo_forecast(lat: float, lon: float) -> dict[str, Any]:
    """7-day daily forecast from Open-Meteo for a point.

    Returns the raw-ish normalized ``daily`` block plus metadata. Raises
    :class:`WeatherProviderError` on any failure; the caller decides whether to
    degrade to ``state: "unavailable"``.
    """
    _validate_coords(lat, lon)
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(
                [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                ]
            ),
            "forecast_days": _FORECAST_DAYS,
            "timezone": _TIMEZONE,
        }
    )
    data = _http_json(f"{_OPEN_METEO_URL}?{query}")
    daily = data.get("daily") or {}
    days = daily.get("time") or []
    if not days:
        raise WeatherProviderError("open_meteo_no_data", "forecast returned no days")

    records = []
    for i, day in enumerate(days):
        records.append(
            {
                "date": day,
                "temperature_max_c": _at(daily.get("temperature_2m_max"), i),
                "temperature_min_c": _at(daily.get("temperature_2m_min"), i),
                "precipitation_mm": _at(daily.get("precipitation_sum"), i),
                "precipitation_probability_percent": _at(
                    daily.get("precipitation_probability_max"), i
                ),
                "wind_speed_max_kmh": _at(daily.get("wind_speed_10m_max"), i),
            }
        )

    return {
        "provider": "open-meteo",
        "kind": "forecast",
        "timezone": data.get("timezone", _TIMEZONE),
        "retrieved_at": _now_iso(),
        "forecast_days": len(records),
        "daily": records,
    }


@lru_cache(maxsize=128)
def _fetch_nasa_power_cached(latitude: float, longitude: float, as_of_day: str) -> dict[str, Any]:
    """Cached NASA POWER fetch keyed on (rounded lat, rounded lon, day).

    ``as_of_day`` is an ISO date string so the cache key is stable within a day
    (POWER data only advances daily, and trails ~5 days behind).
    """
    as_of = date.fromisoformat(as_of_day)
    end_day = as_of - timedelta(days=_NASA_LAG_DAYS)
    start_day = end_day - timedelta(days=_NASA_WINDOW_DAYS)

    query = urllib.parse.urlencode(
        {
            "parameters": "T2M,PRECTOTCORR,RH2M",
            "community": "AG",
            "latitude": latitude,
            "longitude": longitude,
            "start": start_day.strftime("%Y%m%d"),
            "end": end_day.strftime("%Y%m%d"),
            "format": "JSON",
        }
    )
    data = _http_json(f"{_NASA_POWER_URL}?{query}")
    params = (((data or {}).get("properties") or {}).get("parameter")) or {}
    temps = params.get("T2M") or {}
    rains = params.get("PRECTOTCORR") or {}
    humidity = params.get("RH2M") or {}

    # Keep only days with a valid temperature AND rainfall reading.
    valid_days = sorted(
        day
        for day in (set(temps) & set(rains))
        if _is_finite_reading(temps.get(day)) and _is_finite_reading(rains.get(day))
    )
    if not valid_days:
        raise WeatherProviderError("nasa_power_no_data", "no valid POWER observations in window")

    daily = []
    temp_values: list[float] = []
    rain_total = 0.0
    humidity_values: list[float] = []
    for day in valid_days:
        t = float(temps[day])
        r = float(rains[day])
        h = humidity.get(day)
        temp_values.append(t)
        rain_total += r
        record = {
            "date": f"{day[:4]}-{day[4:6]}-{day[6:8]}",
            "temperature_c": round(t, 2),
            "precipitation_mm": round(r, 2),
            "relative_humidity_percent": None,
        }
        if _is_finite_reading(h):
            hv = float(h)
            humidity_values.append(hv)
            record["relative_humidity_percent"] = round(hv, 2)
        daily.append(record)

    summary = {
        "mean_temperature_c": round(sum(temp_values) / len(temp_values), 2),
        "precipitation_total_mm": round(rain_total, 2),
        "mean_relative_humidity_percent": (
            round(sum(humidity_values) / len(humidity_values), 2) if humidity_values else None
        ),
    }

    return {
        "provider": "nasa-power",
        "kind": "observed",
        "observation_scale": (
            "area-level point-grid data, roughly 50 km resolution; not field-level"
        ),
        "period": {"start": daily[0]["date"], "end": daily[-1]["date"]},
        "retrieved_at": _now_iso(),
        "summary": summary,
        "daily": daily,
    }


def fetch_nasa_power(lat: float, lon: float, as_of: date | None = None) -> dict[str, Any]:
    """Observed-climate context from NASA POWER for a point.

    Coordinates are rounded to 0.1 deg (POWER's grid is coarse anyway) which
    also widens cache hits. Raises :class:`WeatherProviderError` on failure.
    """
    _validate_coords(lat, lon)
    as_of_day = (as_of or date.today()).isoformat()
    return _fetch_nasa_power_cached(round(lat, 1), round(lon, 1), as_of_day)


def fetch_weather(lat: float, lon: float) -> dict[str, Any]:
    """Fetch both providers in parallel; degrade gracefully per provider.

    Returns a dict with ``forecast`` and ``nasa_power`` blocks, each wrapped in
    ``{"state": "available"|"unavailable", ...}`` so a single upstream outage
    never fails the whole call. ``coordinates`` echoes the request.
    """
    _validate_coords(lat, lon)

    forecast_future = _UPSTREAM_POOL.submit(fetch_open_meteo_forecast, lat, lon)
    nasa_future = _UPSTREAM_POOL.submit(fetch_nasa_power, lat, lon)

    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "retrieved_at": _now_iso(),
        "forecast": _settle(forecast_future),
        "nasa_power": _settle(nasa_future),
    }


# ── Small helpers ──────────────────────────────────────────────────────────────
def _settle(future) -> dict[str, Any]:
    """Resolve a provider future into an available/unavailable envelope."""
    try:
        return {"state": "available", "data": future.result()}
    except WeatherProviderError as exc:
        return {"state": "unavailable", "reason": exc.code, "detail": str(exc)}
    except Exception as exc:  # defensive: never let one provider crash the call
        return {"state": "unavailable", "reason": "unexpected_error", "detail": str(exc)}


def _at(seq: list[Any] | None, index: int) -> Any:
    """Safe indexed access returning None when missing."""
    if not seq or index >= len(seq):
        return None
    return seq[index]


def _is_finite_reading(value: Any) -> bool:
    """True when ``value`` is a real reading (finite and not POWER's sentinel)."""
    if value is None:
        return False
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(num) and num != _NASA_SENTINEL
