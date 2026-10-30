"""NASA POWER daily point-data request construction and normalization."""

from __future__ import annotations

import math
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.contracts.challenge.v1 import (
    ClimateVariableCoverage,
    DailyClimateObservation,
    DistrictClimateBundle,
    DistrictClimateBundleManifest,
    SourceProvenance,
)
from app.contracts.challenge.ports import ArtifactNotFound

POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_DOCS_URL = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
POWER_PARAMETERS = {
    "PRECTOTCORR": ("rainfall_mm", "mm/day"),
    "T2M": ("temperature_c", "°C"),
    "ALLSKY_SFC_SW_DWN": ("solar_mj_m2_day", "MJ/m²/day"),
}
POWER_FILL_VALUE = -999.0
POWER_TIMEOUT_SECONDS = 45
POWER_RESOLUTION_METERS = 50_000


def _request_power(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "FieldShiftBD/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=POWER_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise RuntimeError(f"NASA POWER returned HTTP {response.status}")
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"NASA POWER returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"NASA POWER request failed: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("NASA POWER returned invalid JSON") from error


class NasaPowerHistoryProvider:
    """Fetch normalized POWER daily histories and keep a persistent JSON cache."""

    def __init__(self, cache_root: Path, *, clock=None) -> None:
        self._cache_root = Path(cache_root).resolve() / "power-history"
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_bundle(
        self,
        district_code: str,
        latitude: float,
        longitude: float,
        start: date,
        end: date,
        *,
        offline: bool = False,
    ) -> DistrictClimateBundle:
        url = build_power_daily_url(latitude, longitude, start, end)
        key_material = f"{district_code}|{latitude:.4f}|{longitude:.4f}|{start}|{end}"
        key = hashlib.sha256(key_material.encode()).hexdigest()
        cache_file = self._cache_root / key[:2] / f"{key}.json"
        if offline:
            if not cache_file.is_file():
                raise ArtifactNotFound("no cached NASA POWER history for this location and period")
            return DistrictClimateBundle.model_validate_json(cache_file.read_bytes())

        payload = _request_power(url)
        observations, coverages = parse_power_daily_response(payload, start, end)
        if not observations:
            raise ValueError("NASA POWER returned no complete daily observations")
        now = self._clock()
        bundle_id = f"power-{key}"
        provenance = SourceProvenance(
            source_id="nasa-power-daily-point",
            source_name="NASA POWER Daily Point",
            source_url=POWER_DOCS_URL,
            dataset_version="POWER Daily API",
            retrieved_at=now,
            recorded_at=now,
            method="nasa_power",
            temporal_start=start,
            temporal_end=end,
            spatial_resolution_m=POWER_RESOLUTION_METERS,
            quality_status="verified",
        )
        bundle = DistrictClimateBundle(
            contract_version="1.0.0",
            manifest=DistrictClimateBundleManifest(
                contract_version="1.0.0",
                district_code=district_code,
                bundle_id=bundle_id,
                created_at=now,
                coverage_start=start,
                coverage_end=end,
                assets=[],
                coverage_by_variable=coverages,
                provenance=[provenance],
                quality_status="verified",
            ),
            daily_series=observations,
        )
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{key}.", suffix=".tmp", dir=cache_file.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as cache_stream:
                cache_stream.write(bundle.model_dump_json())
                cache_stream.flush()
                os.fsync(cache_stream.fileno())
            os.replace(temporary_path, cache_file)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
        return bundle


def build_power_daily_url(
    latitude: float, longitude: float, start: date, end: date
) -> str:
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("latitude must be finite and between -90 and 90")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("longitude must be finite and between -180 and 180")
    if end < start:
        raise ValueError("end must not precede start")
    query = urllib.parse.urlencode(
        {
            "parameters": ",".join(POWER_PARAMETERS),
            "community": "AG",
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
            "time-standard": "UTC",
        }
    )
    return f"{POWER_DAILY_URL}?{query}"


def parse_power_daily_response(
    payload: dict[str, Any], start: date, end: date
) -> tuple[list[DailyClimateObservation], list[ClimateVariableCoverage]]:
    """Normalize POWER data, retaining gaps through coverage counts and dates."""
    if end < start:
        raise ValueError("end must not precede start")
    parameters = payload.get("parameters") or (
        (payload.get("properties") or {}).get("parameter") or {}
    )
    expected_days = (end - start).days + 1
    expected_keys = [
        (start + timedelta(days=offset)).strftime("%Y%m%d")
        for offset in range(expected_days)
    ]
    values_by_parameter: dict[str, dict[str, float | None]] = {}
    coverages: list[ClimateVariableCoverage] = []

    for parameter, (variable, units) in POWER_PARAMETERS.items():
        raw_values = parameters.get(parameter) or {}
        normalized: dict[str, float | None] = {}
        for key in expected_keys:
            try:
                value = float(raw_values[key])
            except (KeyError, TypeError, ValueError):
                normalized[key] = None
                continue
            normalized[key] = (
                None if not math.isfinite(value) or value == POWER_FILL_VALUE else value
            )
        values_by_parameter[parameter] = normalized
        valid = sum(value is not None for value in normalized.values())
        status = "available" if valid == expected_days else "partial" if valid else "unavailable"
        coverages.append(
            ClimateVariableCoverage(
                variable=variable,
                units=units,
                status=status,
                expected_observations=expected_days,
                valid_observations=valid,
                missing_observations=expected_days - valid,
            )
        )

    observations: list[DailyClimateObservation] = []
    for key in expected_keys:
        rainfall = values_by_parameter["PRECTOTCORR"][key]
        temperature = values_by_parameter["T2M"][key]
        solar_kwh = values_by_parameter["ALLSKY_SFC_SW_DWN"][key]
        if rainfall is None or temperature is None or solar_kwh is None:
            continue
        if rainfall < 0 or solar_kwh < 0:
            continue
        observations.append(
            DailyClimateObservation(
                date=date(int(key[:4]), int(key[4:6]), int(key[6:8])),
                rainfall_mm=rainfall,
                temperature_c=temperature,
                solar_mj_m2_day=solar_kwh * 3.6,
            )
        )
    return observations, coverages
