"""Read pinned public-source captures only when their SHA-256 matches the manifest."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CAPTURE_ROOT = Path(__file__).resolve().parents[1] / "data" / "source_captures" / "barc_crop_zoning"
MANIFEST_PATH = CAPTURE_ROOT / "capture_manifest.json"


class SourceCaptureError(ValueError):
    """A capture is missing, unlisted, or does not match its pinned digest."""


@lru_cache(maxsize=1)
def capture_manifest() -> dict[str, dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        raise SourceCaptureError("capture_manifest.json is missing; run scripts.capture_barc_portal_sources")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {entry["path"]: entry for entry in manifest["files"]}


def capture_entry(relative_path: str) -> dict[str, Any]:
    entry = capture_manifest().get(relative_path)
    if entry is None:
        raise SourceCaptureError(f"{relative_path} is not listed in the capture manifest")
    return entry


@lru_cache(maxsize=512)
def read_verified_bytes(relative_path: str) -> bytes:
    entry = capture_entry(relative_path)
    path = CAPTURE_ROOT / relative_path
    if not path.is_file():
        raise SourceCaptureError(f"{relative_path} is missing")
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest().upper()
    if digest != entry["sha256"]:
        raise SourceCaptureError(f"{relative_path} does not match its pinned SHA-256")
    return body


def read_verified_json(relative_path: str) -> Any:
    return json.loads(read_verified_bytes(relative_path).decode("utf-8"))
