"""Publish an explicitly sourced district sampling point into the read cache."""

import hashlib
import os
from pathlib import Path
import tempfile

from app.contracts.challenge.v1 import ClimateSamplingPoint, DistrictClimateBundle
from app.services.m1_reference import geography


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
    manifest = bundle.manifest.model_copy(update={"sampling_point": sampling_point}, deep=True)
    published = bundle.model_copy(update={"manifest": manifest}, deep=True)
    payload = published.model_dump_json().encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    versions = directory / "versions"
    if not versions.resolve().is_relative_to(root):
        raise ValueError("version cache path escapes cache root")
    versions.mkdir(parents=True, exist_ok=True)
    version = versions / f"{digest}.json"
    if not version.exists():
        _atomic_write(version, payload)
    target = directory / "bundle.json"
    _atomic_write(target, payload)
    return target
