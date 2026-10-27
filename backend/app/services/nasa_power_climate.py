"""Historical NASA POWER context for rotation comparisons.

This data is descriptive climate evidence, not a field measurement or a crop
suitability model. Complete daily histories are cached on disk so deployments
with a persistent cache mount do not repeatedly download the same series.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_DOCS_URL = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
POWER_RESOLUTION_URL = "https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/"
OBSERVATION_SCALE = (
    "NASA POWER meteorological data are approximately 0.5° × 0.625° "
    "(roughly 50–60 km scale near Bangladesh); this is grid-cell context, "
    "not field-level measurement."
)
PARAMETERS = ("T2M", "PRECTOTCORR")
TIMEOUT_SECONDS = 30
MIN_COVERAGE_PERCENT = 90.0


class NasaPowerHistoryError(RuntimeError):
    """An expected upstream or response error for a historical POWER request."""


def _cache_dir() -> Path:
    return Path(os.getenv("NASA_POWER_CACHE_DIR", "/tmp/fieldshift-nasa-power-cache"))


def _finite(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number != -999.0


def _period_stats(years: list[dict[str, Any]], start: int, end: int) -> dict[str, Any]:
    available = [row for row in years if start <= row["year"] <= end]
    selected = [row for row in available if row["coverage_percent"] >= MIN_COVERAGE_PERCENT]
    observed_days = sum(row["days_observed"] for row in available)
    expected_days = sum(366 if calendar.isleap(year) else 365 for year in range(start, end + 1))
    years_in_period = end - start + 1
    if not selected:
        return {
            "start_year": start,
            "end_year": end,
            "years_observed": 0,
            "years_available": years_in_period,
            "mean_annual_rainfall_mm": None,
            "mean_annual_temperature_c": None,
            "observed_days": observed_days,
            "expected_days": expected_days,
            "coverage_percent": round(100 * observed_days / expected_days, 2),
            "annual_values": [],
        }
    return {
        "start_year": start,
        "end_year": end,
        "years_observed": len(selected),
        "years_available": years_in_period,
        "mean_annual_rainfall_mm": round(
            sum(row["rainfall_total_mm"] for row in selected) / len(selected), 1
        ),
        "mean_annual_temperature_c": round(
            sum(row["mean_temperature_c"] for row in selected) / len(selected), 2
        ),
        "observed_days": observed_days,
        "expected_days": expected_days,
        "coverage_percent": round(100 * observed_days / expected_days, 2),
        "annual_values": selected,
    }


def _summarize(data: dict[str, Any], start_year: int, end_year: int) -> dict[str, Any]:
    parameters = (((data.get("properties") or {}).get("parameter")) or {})
    temperatures = parameters.get("T2M") or {}
    precipitation = parameters.get("PRECTOTCORR") or {}
    by_year: dict[int, dict[str, Any]] = {}
    by_year_month: dict[tuple[int, int], dict[str, Any]] = {}
    observed_dates: list[str] = []
    for key in sorted(set(temperatures) & set(precipitation)):
        if len(key) != 8 or not _finite(temperatures[key]) or not _finite(precipitation[key]):
            continue
        year = int(key[:4])
        if year < start_year or year > end_year:
            continue
        row = by_year.setdefault(
            year,
            {
                "year": year,
                "rainfall_total_mm": 0.0,
                "temperature_sum": 0.0,
                "days_observed": 0,
            },
        )
        row["rainfall_total_mm"] += float(precipitation[key])
        row["temperature_sum"] += float(temperatures[key])
        row["days_observed"] += 1
        month = int(key[4:6])
        month_row = by_year_month.setdefault(
            (year, month),
            {
                "precipitation_total_mm": 0.0,
                "temperature_sum": 0.0,
                "days_observed": 0,
            },
        )
        month_row["precipitation_total_mm"] += float(precipitation[key])
        month_row["temperature_sum"] += float(temperatures[key])
        month_row["days_observed"] += 1
        observed_dates.append(f"{key[:4]}-{key[4:6]}-{key[6:8]}")

    annual = []
    for year in sorted(by_year):
        row = by_year[year]
        count = row["days_observed"]
        expected_days = 366 if calendar.isleap(year) else 365
        annual.append(
            {
                "year": year,
                "rainfall_total_mm": round(row["rainfall_total_mm"], 1),
                "mean_temperature_c": round(row["temperature_sum"] / count, 2),
                "days_observed": count,
                "days_expected": expected_days,
                "coverage_percent": round(100 * count / expected_days, 1),
            }
        )
    split_year = start_year + (end_year - start_year + 1) // 2 - 1
    earlier = _period_stats(annual, start_year, split_year)
    later = _period_stats(annual, split_year + 1, end_year)
    monthly_comparison = []
    for month in range(1, 13):
        monthly_periods = []
        for period_start, period_end in ((start_year, split_year), (split_year + 1, end_year)):
            available_values = [
                (year, by_year_month[(year, month)])
                for year in range(period_start, period_end + 1)
                if (year, month) in by_year_month
            ]
            expected_days = sum(
                calendar.monthrange(year, month)[1]
                for year in range(period_start, period_end + 1)
            )
            observed_days = sum(value["days_observed"] for _, value in available_values)
            values = [
                (year, value)
                for year, value in available_values
                if (
                    100 * value["days_observed"] / calendar.monthrange(year, month)[1]
                    >= MIN_COVERAGE_PERCENT
                )
            ]
            monthly_periods.append(
                {
                    "years_observed": len(values),
                    "years_available": period_end - period_start + 1,
                    "mean_monthly_rainfall_mm": (
                        round(
                            sum(value["precipitation_total_mm"] for _, value in values)
                            / len(values),
                            1,
                        )
                        if values
                        else None
                    ),
                    "mean_temperature_c": (
                        round(
                            sum(
                                value["temperature_sum"] / value["days_observed"]
                                for _, value in values
                            )
                            / len(values),
                            2,
                        )
                        if values
                        else None
                    ),
                    "observed_days": observed_days,
                    "expected_days": expected_days,
                    "coverage_percent": (
                        round(100 * observed_days / expected_days, 2)
                        if expected_days
                        else 0.0
                    ),
                }
            )
        early, recent = monthly_periods
        monthly_comparison.append({
            "month": month,
            "earlier": early,
            "later": recent,
            "difference_later_minus_earlier": {
                "rainfall_mm": (
                    round(recent["mean_monthly_rainfall_mm"] - early["mean_monthly_rainfall_mm"], 1)
                    if early["mean_monthly_rainfall_mm"] is not None
                    and recent["mean_monthly_rainfall_mm"] is not None
                    else None
                ),
                "temperature_c": (
                    round(recent["mean_temperature_c"] - early["mean_temperature_c"], 2)
                    if early["mean_temperature_c"] is not None
                    and recent["mean_temperature_c"] is not None
                    else None
                ),
            },
        })
    return {
        "requested_period": {"start": f"{start_year}-01-01", "end": f"{end_year}-12-31"},
        "observed_period": {"start": min(observed_dates) if observed_dates else None,
                            "end": max(observed_dates) if observed_dates else None},
        "annual_values": [row for row in annual if row["coverage_percent"] >= MIN_COVERAGE_PERCENT],
        "monthly_comparison": monthly_comparison,
        "period_comparison": {
            "earlier": earlier,
            "later": later,
            "difference_later_minus_earlier": {
                "annual_rainfall_mm": (
                    round(later["mean_annual_rainfall_mm"] - earlier["mean_annual_rainfall_mm"], 1)
                    if earlier["mean_annual_rainfall_mm"] is not None
                    and later["mean_annual_rainfall_mm"] is not None
                    else None
                ),
                "annual_mean_temperature_c": (
                    round(later["mean_annual_temperature_c"] - earlier["mean_annual_temperature_c"], 2)
                    if earlier["mean_annual_temperature_c"] is not None
                    and later["mean_annual_temperature_c"] is not None
                    else None
                ),
            },
        },
    }


def _request_power(latitude: float, longitude: float, start_year: int, end_year: int) -> dict[str, Any]:
    query = urllib.parse.urlencode({
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": f"{start_year}0101",
        "end": f"{end_year}1231",
        "time-standard": "UTC",
        "format": "JSON",
    })
    request = urllib.request.Request(
        f"{POWER_DAILY_URL}?{query}",
        headers={"User-Agent": "FieldShiftBD/1.0 (historical climate context)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise NasaPowerHistoryError(f"NASA POWER returned HTTP {response.status}")
            payload = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NasaPowerHistoryError(f"NASA POWER history could not be retrieved: {exc}") from exc
    if not (((payload.get("properties") or {}).get("parameter")) or {}).get("T2M"):
        raise NasaPowerHistoryError("NASA POWER returned no temperature series")
    return payload


def fetch_rotation_climate(latitude: float | None, longitude: float | None) -> dict[str, Any]:
    """Return annual POWER climate context with truthful retrieval/cache status."""
    common = {
        "dataset": "NASA POWER Daily API, Agroclimatology community",
        "source_reference": POWER_DOCS_URL,
        "resolution_reference": POWER_RESOLUTION_URL,
        "time_standard": "UTC",
        "parameters": [
            {
                "code": "PRECTOTCORR",
                "label": "Corrected precipitation",
                "unit": "mm/day; summed by calendar year",
            },
            {"code": "T2M", "label": "2 m air temperature", "unit": "°C; averaged by calendar year"},
        ],
        "observation_scale": OBSERVATION_SCALE,
        "retrieved_at": None,
        "cache_status": "unavailable",
        "requested_period": None,
        "observed_period": None,
        "annual_values": [],
        "period_comparison": None,
        "monthly_comparison": [],
        "unavailable_reason": None,
    }
    # Leave a one-week buffer so the latest calendar year is not considered
    # complete while NASA's near-real-time daily feed is still catching up.
    end_year = (date.today() - timedelta(days=7)).year - 1
    start_year = end_year - 24
    common["requested_period"] = {
        "start": f"{start_year}-01-01",
        "end": f"{end_year}-12-31",
    }
    if latitude is None or longitude is None:
        return {**common, "unavailable_reason": "Farm coordinates are not recorded."}

    # NASA POWER provides a 0.5-degree grid. Round coordinates consistently
    # with the existing weather provider's cache convention.
    lat, lon = round(float(latitude), 1), round(float(longitude), 1)
    common["requested_coordinate"] = {"latitude": float(latitude), "longitude": float(longitude)}
    common["query_coordinate"] = {"latitude": lat, "longitude": lon}
    key = hashlib.sha256(
        f"{lat:.1f}|{lon:.1f}|{start_year}|{end_year}|{','.join(PARAMETERS)}".encode()
    ).hexdigest()
    cache_file = _cache_dir() / f"{key}.json"
    cache_writable = True
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        cache_writable = False
    retrieved_at = datetime.now(timezone.utc).isoformat()

    cached: dict[str, Any] | None = None
    if cache_writable and cache_file.is_file():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cached = None

    refresh = os.getenv("NASA_POWER_REFRESH_CACHE", "0").strip() == "1"
    if cached is not None and not refresh:
        payload = cached.get("payload") or {}
        summary = _summarize(payload, start_year, end_year)
        if summary["observed_period"]["start"]:
            if not summary["annual_values"]:
                common["unavailable_reason"] = (
                    "No annual values met the 90% daily-coverage threshold; period coverage is shown below."
                )
            return {
                **common,
                "retrieved_at": cached.get("retrieved_at"),
                "cache_status": "disk_cache",
                **summary,
            }
        cached = None

    try:
        payload = _request_power(lat, lon, start_year, end_year)
        envelope = {"payload": payload, "retrieved_at": retrieved_at}
        if cache_writable:
            temporary_path = ""
            try:
                fd, temporary_path = tempfile.mkstemp(
                    prefix=f".{key}.", suffix=".tmp", dir=cache_file.parent
                )
                with os.fdopen(fd, "w", encoding="utf-8") as target:
                    json.dump(envelope, target, separators=(",", ":"))
                os.replace(temporary_path, cache_file)
                cache_status = "live"
            except OSError:
                cache_status = "live_uncached"
            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)
        else:
            cache_status = "live_uncached"
        cached = envelope
    except NasaPowerHistoryError:  # stale disk data is preferable to a missing comparison
        if cached is None:
            return {**common, "unavailable_reason": "Historical NASA POWER data is unavailable right now."}
        cache_status = "stale_cache"
        common["unavailable_reason"] = "Live NASA POWER retrieval failed; showing the last cached response."

    payload = cached.get("payload") or {}
    summary = _summarize(payload, start_year, end_year)
    if not summary["observed_period"]["start"]:
        return {**common, "unavailable_reason": "NASA POWER returned no usable daily observations for this period."}
    if not summary["annual_values"]:
        common["unavailable_reason"] = (
            "No annual values met the 90% daily-coverage threshold; period coverage is shown below."
        )
    return {
        **common,
        "retrieved_at": cached.get("retrieved_at"),
        "cache_status": cache_status,
        **summary,
    }
