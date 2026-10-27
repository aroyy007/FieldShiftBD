from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

from app.services import nasa_power_climate


def _daily_sample() -> dict:
    parameters = {"T2M": {}, "PRECTOTCORR": {}}
    for year in range(2001, 2026):
        day = date(year, 1, 1)
        end = date(year + 1, 1, 1)
        while day < end:
            key = day.strftime("%Y%m%d")
            parameters["T2M"][key] = str(20 + (year - 2001) / 10)
            parameters["PRECTOTCORR"][key] = "2.0"
            day += timedelta(days=1)
    parameters["T2M"]["20010201"] = "-999"
    return {"properties": {"parameter": parameters}}


def test_summarize_uses_two_periods_and_omits_missing_values() -> None:
    summary = nasa_power_climate._summarize(_daily_sample(), 2001, 2025)

    assert summary["requested_period"] == {"start": "2001-01-01", "end": "2025-12-31"}
    assert len(summary["annual_values"]) == 25
    assert summary["annual_values"][0]["days_observed"] == 364
    assert summary["annual_values"][0]["coverage_percent"] > 90
    assert summary["period_comparison"]["earlier"]["start_year"] == 2001
    assert summary["period_comparison"]["earlier"]["end_year"] == 2012
    assert summary["period_comparison"]["later"]["start_year"] == 2013
    assert summary["period_comparison"]["later"]["end_year"] == 2025
    assert summary["period_comparison"]["earlier"]["years_observed"] == 12
    assert len(summary["monthly_comparison"]) == 12


def test_sparse_years_and_months_do_not_enter_climate_means() -> None:
    sample = {
        "properties": {
            "parameter": {
                "T2M": {"20010101": 20, "20130101": 21},
                "PRECTOTCORR": {"20010101": 2, "20130101": 3},
            }
        }
    }

    summary = nasa_power_climate._summarize(sample, 2001, 2025)

    assert summary["annual_values"] == []
    assert summary["period_comparison"]["earlier"]["mean_annual_rainfall_mm"] is None
    assert summary["period_comparison"]["earlier"]["years_observed"] == 0
    assert summary["period_comparison"]["earlier"]["years_available"] == 12
    assert summary["period_comparison"]["earlier"]["coverage_percent"] > 0
    january = summary["monthly_comparison"][0]
    assert january["earlier"]["years_available"] == 12
    assert january["earlier"]["mean_monthly_rainfall_mm"] is None
    assert january["later"]["mean_monthly_rainfall_mm"] is None


def test_fetch_rotation_climate_uses_disk_cache_without_refetch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NASA_POWER_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("NASA_POWER_REFRESH_CACHE", raising=False)
    sample = _daily_sample()
    with patch.object(nasa_power_climate, "_request_power", return_value=sample) as request:
        first = nasa_power_climate.fetch_rotation_climate(23.8, 90.4)
        second = nasa_power_climate.fetch_rotation_climate(23.8, 90.4)

    assert first["cache_status"] == "live"
    assert second["cache_status"] == "disk_cache"
    assert second["retrieved_at"] == first["retrieved_at"]
    request.assert_called_once()


def test_failed_refresh_returns_stale_cache_and_missing_coordinates_are_unavailable(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("NASA_POWER_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("NASA_POWER_REFRESH_CACHE", "1")
    with patch.object(nasa_power_climate, "_request_power", return_value=_daily_sample()):
        nasa_power_climate.fetch_rotation_climate(23.8, 90.4)
    with patch.object(
        nasa_power_climate,
        "_request_power",
        side_effect=nasa_power_climate.NasaPowerHistoryError("offline"),
    ):
        stale = nasa_power_climate.fetch_rotation_climate(23.8, 90.4)

    missing = nasa_power_climate.fetch_rotation_climate(None, None)
    assert stale["cache_status"] == "stale_cache"
    assert stale["unavailable_reason"]
    assert missing["cache_status"] == "unavailable"
    assert missing["unavailable_reason"] == "Farm coordinates are not recorded."
