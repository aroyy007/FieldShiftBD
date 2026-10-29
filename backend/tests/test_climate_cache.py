import hashlib
import socket
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.challenge.ports import ArtifactNotFound, AdapterConflict, StaleArtifact
from app.contracts.challenge.v1 import ClimateAssetManifest, DistrictClimateBundle
from app.services.climate.cache import ClimateBundleCache, CorruptClimateCache

NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)
ASSET_CONTENT = b"SYNTHETIC TEST ONLY\ndate,rainfall_mm\n2026-10-01,4.2\n"


def _bundle(district_code="SYN-81", *, expires_at="2026-10-30T00:00:00Z", relative_path="SYN-81/rainfall.csv"):
    return DistrictClimateBundle.model_validate(
        {
            "contract_version": "1.0.0",
            "manifest": {
                "contract_version": "1.0.0",
                "district_code": district_code,
                "bundle_id": "synthetic-syn-81-v1",
                "created_at": "2026-10-28T00:00:00Z",
                "expires_at": expires_at,
                "coverage_start": "2026-10-01",
                "coverage_end": "2026-10-01",
                "quality_status": "synthetic",
                "assets": [
                    {
                        "asset_id": "synthetic-rainfall",
                        "source_name": "SYNTHETIC TEST ONLY",
                        "dataset_id": "synthetic-daily-rainfall",
                        "dataset_version": "fixture-v1",
                        "variable": "rainfall",
                        "units": "mm/day",
                        "temporal_resolution": "daily",
                        "coverage_start": "2026-10-01",
                        "coverage_end": "2026-10-01",
                        "relative_path": relative_path,
                        "checksum_sha256": hashlib.sha256(ASSET_CONTENT).hexdigest(),
                        "size_bytes": len(ASSET_CONTENT),
                        "license": "synthetic test data",
                        "quality_status": "synthetic",
                    }
                ],
                "provenance": [],
            },
            "daily_series": [
                {
                    "date": "2026-10-01",
                    "rainfall_mm": 4.2,
                    "temperature_c": 28.1,
                    "solar_mj_m2_day": 18.0,
                }
            ],
        }
    )


def _write_cache(root, bundle):
    district_dir = root / "SYN-81"
    district_dir.mkdir(parents=True, exist_ok=True)
    asset_path = root / bundle.manifest.assets[0].relative_path
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(ASSET_CONTENT)
    (district_dir / "bundle.json").write_text(
        bundle.model_dump_json(), encoding="utf-8"
    )


def test_local_cache_returns_validated_synthetic_fixture_without_network(tmp_path, monkeypatch):
    bundle = _bundle()
    _write_cache(tmp_path, bundle)

    def network_forbidden(*_args, **_kwargs):
        raise AssertionError("cache reads must never use the network")

    monkeypatch.setattr(socket, "socket", network_forbidden)
    cached = ClimateBundleCache(tmp_path, clock=lambda: NOW).load_bundle("SYN-81")

    assert cached.manifest.quality_status == "synthetic"
    assert cached.daily_series[0].rainfall_mm == 4.2


def test_local_cache_distinguishes_missing_expired_and_corrupt_bundles(tmp_path):
    cache = ClimateBundleCache(tmp_path, clock=lambda: NOW)
    with pytest.raises(ArtifactNotFound):
        cache.load_bundle("SYN-81")

    expired = _bundle(expires_at="2026-10-29T00:00:00Z")
    _write_cache(tmp_path, expired)
    with pytest.raises(StaleArtifact):
        cache.load_bundle("SYN-81")

    current = _bundle()
    _write_cache(tmp_path, current)
    (tmp_path / "SYN-81/rainfall.csv").write_bytes(b"X" * len(ASSET_CONTENT))
    with pytest.raises(CorruptClimateCache, match="checksum"):
        cache.load_bundle("SYN-81")


def test_cache_rejects_path_traversal_unknown_and_mismatched_district(tmp_path):
    with pytest.raises(ValidationError, match="relative_path"):
        ClimateAssetManifest.model_validate(
            {
                "asset_id": "escape",
                "source_name": "SYNTHETIC TEST ONLY",
                "dataset_id": "fixture",
                "dataset_version": "v1",
                "variable": "rain",
                "units": "mm/day",
                "temporal_resolution": "daily",
                "coverage_start": "2026-10-01",
                "coverage_end": "2026-10-01",
                "relative_path": "../outside.csv",
                "checksum_sha256": hashlib.sha256(ASSET_CONTENT).hexdigest(),
                "size_bytes": len(ASSET_CONTENT),
                "license": "synthetic test data",
                "quality_status": "synthetic",
            }
        )

    with pytest.raises(ArtifactNotFound):
        ClimateBundleCache(tmp_path, clock=lambda: NOW).load_bundle("../../outside")

    bundle = _bundle(district_code="SYN-81")
    _write_cache(tmp_path, bundle)
    (tmp_path / "SYN-82").mkdir()
    (tmp_path / "SYN-82/bundle.json").write_text(
        bundle.model_dump_json(), encoding="utf-8"
    )
    with pytest.raises(AdapterConflict):
        ClimateBundleCache(tmp_path, clock=lambda: NOW).load_bundle("SYN-82")


def test_cache_enforces_manifest_asset_and_bundle_byte_limits(tmp_path):
    bundle = _bundle()
    _write_cache(tmp_path, bundle)

    with pytest.raises(CorruptClimateCache, match="manifest exceeds"):
        ClimateBundleCache(tmp_path, clock=lambda: NOW, max_manifest_bytes=16).load_bundle("SYN-81")

    with pytest.raises(CorruptClimateCache, match="asset exceeds"):
        ClimateBundleCache(
            tmp_path,
            clock=lambda: NOW,
            max_asset_bytes=len(ASSET_CONTENT) - 1,
        ).load_bundle("SYN-81")

    with pytest.raises(CorruptClimateCache, match="total byte limit"):
        ClimateBundleCache(
            tmp_path,
            clock=lambda: NOW,
            max_total_asset_bytes=len(ASSET_CONTENT) - 1,
        ).load_bundle("SYN-81")


def test_cache_rejects_non_positive_byte_limits(tmp_path):
    with pytest.raises(ValueError, match="must be positive"):
        ClimateBundleCache(tmp_path, max_manifest_bytes=0)


def test_cache_maps_asset_disappearing_after_stat_to_typed_corruption(tmp_path, monkeypatch):
    _write_cache(tmp_path, _bundle())
    original_open = Path.open

    def disappear_asset(path, *args, **kwargs):
        if path.name == "rainfall.csv":
            raise FileNotFoundError(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", disappear_asset)
    with pytest.raises(CorruptClimateCache, match="disappeared while reading"):
        ClimateBundleCache(tmp_path, clock=lambda: NOW).load_bundle("SYN-81")
