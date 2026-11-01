"""Publish an explicitly sourced district sampling point into the read cache."""

import hashlib
import json
import os
from pathlib import Path
import tempfile

from app.contracts.challenge.v1 import (
    ClimateAssetManifest,
    ClimateSamplingPoint,
    DistrictClimateBundle,
)
from app.services.m1_reference import geography
from app.services.climate.parquet_codec import CACHE_FORMAT, encode_daily_series

MAX_PRIOR_INDEX_BYTES = 64 * 1024 * 1024


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".district-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.stat().st_size != len(payload):
            raise ValueError("immutable cache file does not match its content address")
        with path.open("rb") as stream:
            existing = stream.read(len(payload) + 1)
        if existing != payload:
            raise ValueError("immutable cache file does not match its content address")
        return
    _atomic_write(path, payload)


def publish_district_bundle(root: Path, district_code: str, bundle: DistrictClimateBundle, point: dict) -> Path:
    if district_code not in geography().districts:
        raise ValueError("district must be a canonical 4-digit Bangladesh code")
    if bundle.manifest.district_code != district_code:
        raise ValueError("bundle district does not match the publication district")
    sampling_point = ClimateSamplingPoint.model_validate(point)
    root = root.resolve()
    directory = (root / district_code).resolve()
    if not directory.is_relative_to(root):
        raise ValueError("district cache path escapes cache root")
    series_payload = encode_daily_series(bundle.daily_series)
    series_checksum = hashlib.sha256(series_payload).hexdigest()
    series_relative_path = f"{district_code}/assets/daily_series/{series_checksum}.parquet"
    series_path = (root / series_relative_path).resolve()
    if not series_path.is_relative_to(root):
        raise ValueError("daily-series cache path escapes cache root")
    series_path.parent.mkdir(parents=True, exist_ok=True)
    _write_immutable(series_path, series_payload)

    # Keep source assets as supplied; only replace this publisher's prior
    # normalized representation. Source reuse terms remain authoritative.
    source_assets = [
        asset for asset in bundle.manifest.assets
        if not asset.asset_id.startswith("fieldshift-daily-series-")
    ]
    series_asset = ClimateAssetManifest(
        asset_id=f"fieldshift-daily-series-{series_checksum[:24]}",
        source_name="FieldShift normalized daily climate cache",
        dataset_id="fieldshift-normalized-daily-climate",
        dataset_version=CACHE_FORMAT,
        variable="daily_series",
        units="typed-columns; see Parquet schema metadata",
        temporal_resolution="daily",
        coverage_start=bundle.manifest.coverage_start,
        coverage_end=bundle.manifest.coverage_end,
        relative_path=series_relative_path,
        checksum_sha256=series_checksum,
        size_bytes=len(series_payload),
        license="Derived local cache; source provenance and reuse terms remain controlling",
        quality_status=bundle.manifest.quality_status,
    )
    manifest = bundle.manifest.model_copy(
        update={"sampling_point": sampling_point, "assets": [*source_assets, series_asset]},
        deep=True,
    )
    index = bundle.model_dump(mode="json", exclude={"daily_series"})
    index.update(
        cache_format=CACHE_FORMAT,
        daily_series_asset_id=series_asset.asset_id,
        daily_series_row_count=len(bundle.daily_series),
        manifest=manifest.model_dump(mode="json"),
    )
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    versions = directory / "versions"
    if not versions.resolve().is_relative_to(root):
        raise ValueError("version cache path escapes cache root")
    versions.mkdir(parents=True, exist_ok=True)
    target = directory / "bundle.json"
    if not target.resolve().is_relative_to(root):
        raise ValueError("existing climate index path escapes cache root")
    if target.is_file():
        previous_size = target.stat().st_size
        if previous_size > MAX_PRIOR_INDEX_BYTES:
            raise ValueError("existing climate index exceeds the safe archival byte limit")
        previous_payload = target.read_bytes()
        previous_digest = hashlib.sha256(previous_payload).hexdigest()
        previous_version = versions / f"{previous_digest}.json"
        if not previous_version.resolve().is_relative_to(root):
            raise ValueError("previous climate index version escapes cache root")
        _write_immutable(previous_version, previous_payload)
    version = versions / f"{digest}.json"
    if not version.resolve().is_relative_to(root):
        raise ValueError("climate index version escapes cache root")
    _write_immutable(version, payload)
    _atomic_write(target, payload)
    return target
