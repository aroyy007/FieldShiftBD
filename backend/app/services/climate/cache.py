from __future__ import annotations

import hashlib
import json
import re
import stat
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.contracts.challenge.v1 import (
    CONTRACT_VERSION,
    DistrictClimateBundle,
    DistrictClimateBundleManifest,
)
from app.contracts.challenge.ports import ArtifactNotFound, AdapterConflict, StaleArtifact
from app.core.time_utils import to_utc
from app.services.climate.parquet_codec import (
    CACHE_FORMAT,
    MAX_DAILY_ROWS,
    MAX_PARQUET_BYTES,
    ParquetClimateCacheError,
    decode_daily_series,
)

_DEFAULT_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_DEFAULT_MAX_ASSET_BYTES = 1024 * 1024 * 1024
_DEFAULT_MAX_TOTAL_ASSET_BYTES = 4 * 1024 * 1024 * 1024
_CHECKSUM_CHUNK_BYTES = 1024 * 1024


class CorruptClimateCache(RuntimeError):
    """Cache content failed its manifest or checksum validation."""


class ClimateBundleCache:
    """Read-only, size-bounded local cache that never performs network access."""

    def __init__(
        self,
        root: Path,
        *,
        clock=None,
        max_manifest_bytes: int = _DEFAULT_MAX_MANIFEST_BYTES,
        max_asset_bytes: int = _DEFAULT_MAX_ASSET_BYTES,
        max_total_asset_bytes: int = _DEFAULT_MAX_TOTAL_ASSET_BYTES,
    ) -> None:
        if min(max_manifest_bytes, max_asset_bytes, max_total_asset_bytes) < 1:
            raise ValueError("climate cache byte limits must be positive")
        self._root = root.resolve()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._max_manifest_bytes = max_manifest_bytes
        self._max_asset_bytes = max_asset_bytes
        self._max_total_asset_bytes = max_total_asset_bytes

    def load_bundle(self, district_code: str) -> DistrictClimateBundle:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", district_code):
            raise ArtifactNotFound("district code is not a safe cache key")
        bundle_path = self._resolve(f"{district_code}/bundle.json")
        try:
            manifest_stat = bundle_path.stat()
            if not stat.S_ISREG(manifest_stat.st_mode):
                raise CorruptClimateCache("cache manifest is not a regular file")
            if manifest_stat.st_size > self._max_manifest_bytes:
                raise CorruptClimateCache("cache manifest exceeds the configured byte limit")
            with bundle_path.open("rb") as manifest_file:
                raw_bundle = manifest_file.read(self._max_manifest_bytes + 1)
        except FileNotFoundError as error:
            raise ArtifactNotFound(f"no cached climate bundle for {district_code}") from error
        if len(raw_bundle) > self._max_manifest_bytes:
            raise CorruptClimateCache("cache manifest exceeds the configured byte limit")
        try:
            index = json.loads(raw_bundle)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CorruptClimateCache("cached climate bundle is not valid JSON") from error
        if not isinstance(index, dict):
            raise CorruptClimateCache("cached climate bundle index must be an object")
        cache_format = index.get("cache_format")
        if cache_format is None:
            try:
                bundle = DistrictClimateBundle.model_validate(index)
            except ValidationError as error:
                raise CorruptClimateCache("cached climate bundle failed schema validation") from error
            manifest = bundle.manifest
        else:
            manifest = self._load_parquet_index(index, district_code)
            bundle = None
        if manifest.district_code != district_code:
            raise AdapterConflict("cache directory and bundle district codes do not match")
        now = to_utc(self._clock())
        if manifest.expires_at is not None and to_utc(manifest.expires_at) <= now:
            raise StaleArtifact(f"cached climate bundle for {district_code} is expired")
        declared_total_bytes = sum(asset.size_bytes for asset in manifest.assets)
        if declared_total_bytes > self._max_total_asset_bytes:
            raise CorruptClimateCache("climate bundle assets exceed the configured total byte limit")
        parquet_asset_id = index.get("daily_series_asset_id") if cache_format is not None else None
        daily_series = None
        parquet_asset_matches = 0
        for asset in manifest.assets:
            if asset.size_bytes > self._max_asset_bytes:
                raise CorruptClimateCache(f"cache asset exceeds the configured byte limit: {asset.asset_id}")
            path = self._resolve(asset.relative_path)
            try:
                asset_stat = path.stat()
            except FileNotFoundError as error:
                raise CorruptClimateCache(f"cache asset is missing: {asset.asset_id}") from error
            if not stat.S_ISREG(asset_stat.st_mode):
                raise CorruptClimateCache(f"cache asset is not a regular file: {asset.asset_id}")
            if asset_stat.st_size != asset.size_bytes:
                raise CorruptClimateCache(f"cache asset size does not match its manifest: {asset.asset_id}")
            if asset.asset_id == parquet_asset_id:
                parquet_asset_matches += 1
                if asset.variable != "daily_series" or asset.size_bytes > MAX_PARQUET_BYTES:
                    raise CorruptClimateCache("daily-series Parquet asset metadata is invalid")
                try:
                    with path.open("rb") as asset_file:
                        payload = asset_file.read(MAX_PARQUET_BYTES + 1)
                except FileNotFoundError as error:
                    raise CorruptClimateCache(f"cache asset disappeared while reading: {asset.asset_id}") from error
                if len(payload) != asset.size_bytes or len(payload) > MAX_PARQUET_BYTES:
                    raise CorruptClimateCache(f"cache asset size changed while reading: {asset.asset_id}")
                if hashlib.sha256(payload).hexdigest() != asset.checksum_sha256:
                    raise CorruptClimateCache(f"cache asset failed checksum validation: {asset.asset_id}")
                try:
                    daily_series = decode_daily_series(
                        payload, expected_rows=index["daily_series_row_count"]
                    )
                except (KeyError, ParquetClimateCacheError) as error:
                    raise CorruptClimateCache(str(error)) from error
                continue
            digest = hashlib.sha256()
            actual_size = 0
            try:
                with path.open("rb") as asset_file:
                    while chunk := asset_file.read(_CHECKSUM_CHUNK_BYTES):
                        actual_size += len(chunk)
                        if actual_size > self._max_asset_bytes or actual_size > asset.size_bytes:
                            raise CorruptClimateCache(f"cache asset exceeded its declared size: {asset.asset_id}")
                        digest.update(chunk)
            except FileNotFoundError as error:
                raise CorruptClimateCache(f"cache asset disappeared while reading: {asset.asset_id}") from error
            if digest.hexdigest() != asset.checksum_sha256 or actual_size != asset.size_bytes:
                raise CorruptClimateCache(f"cache asset failed checksum validation: {asset.asset_id}")
        if parquet_asset_id is not None and (parquet_asset_matches != 1 or daily_series is None):
            raise CorruptClimateCache("daily-series Parquet asset is missing or ambiguous")
        if cache_format is not None:
            try:
                bundle = DistrictClimateBundle.model_validate(
                    {
                        "contract_version": index["contract_version"],
                        "manifest": manifest.model_dump(mode="python"),
                        "daily_series": daily_series,
                    }
                )
            except (KeyError, ValidationError) as error:
                raise CorruptClimateCache("cached Parquet bundle failed climate contract validation") from error
        return bundle

    @staticmethod
    def _load_parquet_index(index: dict, district_code: str) -> DistrictClimateBundleManifest:
        if index.get("cache_format") != CACHE_FORMAT:
            raise CorruptClimateCache("cached climate bundle uses an unsupported cache format")
        expected_keys = {
            "contract_version", "manifest", "cache_format",
            "daily_series_asset_id", "daily_series_row_count",
        }
        if set(index) != expected_keys:
            raise CorruptClimateCache("cached Parquet index has mixed or unsupported fields")
        if not isinstance(index.get("daily_series_asset_id"), str) or not index["daily_series_asset_id"]:
            raise CorruptClimateCache("cached Parquet index has no daily-series asset reference")
        try:
            manifest = DistrictClimateBundleManifest.model_validate(index["manifest"])
            # Validate the top-level contract version and forbid a private or
            # inline alternate copy before touching the referenced asset.
            if index["contract_version"] != CONTRACT_VERSION:
                raise ValueError("unsupported climate bundle contract version")
            if manifest.district_code != district_code:
                raise AdapterConflict("cache directory and bundle district codes do not match")
            matches = [asset for asset in manifest.assets if asset.asset_id == index["daily_series_asset_id"]]
            series_assets = [asset for asset in manifest.assets if asset.variable == "daily_series"]
            if len(matches) != 1 or len(series_assets) != 1 or matches != series_assets:
                raise ValueError("daily-series asset reference is missing or ambiguous")
            row_count = index.get("daily_series_row_count")
            if (
                not isinstance(row_count, int)
                or isinstance(row_count, bool)
                or not 1 <= row_count <= MAX_DAILY_ROWS
            ):
                raise ValueError("daily-series row count is outside the supported bounds")
        except AdapterConflict:
            raise
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise CorruptClimateCache("cached Parquet index failed schema validation") from error
        return manifest

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as error:
            raise ArtifactNotFound("cache path escapes the configured root") from error
        return candidate
