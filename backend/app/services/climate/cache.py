from __future__ import annotations

import hashlib
import re
import stat
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.contracts.challenge.v1 import DistrictClimateBundle
from app.contracts.challenge.ports import ArtifactNotFound, AdapterConflict, StaleArtifact
from app.core.time_utils import to_utc

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
            bundle = DistrictClimateBundle.model_validate_json(raw_bundle)
        except ValidationError as error:
            raise CorruptClimateCache("cached climate bundle failed schema validation") from error
        if bundle.manifest.district_code != district_code:
            raise AdapterConflict("cache directory and bundle district codes do not match")
        now = to_utc(self._clock())
        if bundle.manifest.expires_at is not None and to_utc(bundle.manifest.expires_at) <= now:
            raise StaleArtifact(f"cached climate bundle for {district_code} is expired")
        declared_total_bytes = sum(asset.size_bytes for asset in bundle.manifest.assets)
        if declared_total_bytes > self._max_total_asset_bytes:
            raise CorruptClimateCache("climate bundle assets exceed the configured total byte limit")
        for asset in bundle.manifest.assets:
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
        return bundle

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as error:
            raise ArtifactNotFound("cache path escapes the configured root") from error
        return candidate
