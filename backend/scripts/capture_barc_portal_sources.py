"""Capture the public BARC crop-zoning JSON responses used by M1 and M2.

The Agri-Advisory Portal (portal.cropzoning.gov.bd) and its suitability API
(api1.cropzoning.gov.bd) are called anonymously by BARC's own public pages.
This script requests only those documented public routes, rate-limits every
request, and writes each response byte-for-byte with its SHA-256 digest. By
default it captures suitability for every listed district/upazila; repeat
``--district-code BBS_CODE`` to limit that portion to a district subset. It
never logs in, sends credentials, or calls role-gated CZIS/GeoServer services.

Run from ``backend`` (network access required; the app never does this at
runtime):

    python -m scripts.capture_barc_portal_sources

Captured files are inputs to ``python -m scripts.import_reference_data``. The
new capture is staged separately and replaces the active snapshot only after
all requests succeed. Re-run it to refresh the evidence before the 180-day
policy window expires, then review the claim manifest against the refreshed
text.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

CAPTURE_DIR = (
    Path(__file__).resolve().parents[1] / "app" / "data" / "source_captures" / "barc_crop_zoning"
)
PORTAL = "https://portal.cropzoning.gov.bd"
SUITABILITY_API = "https://api1.cropzoning.gov.bd"
USER_AGENT = "FieldShiftBD-evidence-capture/1.0 (public BARC portal data; low-rate)"
REQUEST_INTERVAL_SECONDS = 0.8
MAX_RATE_LIMIT_RETRIES = 6
RATE_LIMIT_BACKOFF_SECONDS = 5.0

# Portal crop ids (from /api/crops-all-info) for the crops in the M1 catalog.
PORTAL_PROD_TECH_CROPS = (36, 4, 5, 3)
PORTAL_VARIETY_LIST_CROPS = (36, 4, 5, 3, 2)
# Variety details are captured for crops whose M2 harvest records use them.
PORTAL_VARIETY_DETAIL_CROPS = (36, 4, 5)

def select_suitability_districts(
    districts: list[dict], district_codes: set[str] | None = None
) -> list[dict]:
    """Return every BARC district by default, or validate an explicit subset."""
    if district_codes is None:
        return districts

    normalized_codes = {str(int(code)) for code in district_codes}
    available_codes = {str(int(item["district_c"])) for item in districts}
    unknown_codes = normalized_codes - available_codes
    if unknown_codes:
        codes = ", ".join(sorted(unknown_codes))
        raise ValueError(f"unknown district code(s): {codes}")
    return [item for item in districts if str(int(item["district_c"])) in normalized_codes]


class Capturer:
    def __init__(self, client: httpx.Client, output_dir: Path = CAPTURE_DIR) -> None:
        self.client = client
        self.output_dir = output_dir
        self.entries: list[dict] = []
        self._last_request_at: float | None = None

    def _wait_for_request_slot(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            delay = REQUEST_INTERVAL_SECONDS - (now - self._last_request_at)
            if delay > 0:
                time.sleep(delay)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _retry_delay(response: httpx.Response, retry_number: int) -> float:
        """Honor server backoff instructions, otherwise use capped exponential backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, min(float(retry_after), 300.0))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after)
                    return max(0.0, min(retry_at.timestamp() - time.time(), 300.0))
                except (TypeError, ValueError, OverflowError):
                    pass
        return min(RATE_LIMIT_BACKOFF_SECONDS * (2 ** retry_number), 300.0)

    def get(self, url: str, relative_path: str) -> bytes:
        for retry_number in range(MAX_RATE_LIMIT_RETRIES + 1):
            self._wait_for_request_slot()
            response = self.client.get(url)
            if response.status_code == 429:
                if retry_number >= MAX_RATE_LIMIT_RETRIES:
                    response.raise_for_status()
                delay = self._retry_delay(response, retry_number)
                print(
                    f"BARC API rate limited this capture; retrying in {delay:.0f}s "
                    f"({retry_number + 1}/{MAX_RATE_LIMIT_RETRIES})",
                    flush=True,
                )
                time.sleep(delay)
                continue
            response.raise_for_status()
            break
        body = response.content
        target = self.output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        self.entries.append({
            "path": relative_path,
            "url": url,
            "retrieved_at": datetime.now(ZoneInfo("Asia/Dhaka")).isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(body).hexdigest().upper(),
            "bytes": len(body),
            "content_type": response.headers.get("content-type"),
        })
        return body

    def get_many(self, requests: list[tuple[str, str]]) -> list[bytes]:
        """Fetch sequentially; public source requests must not overlap."""
        return [self.get(url, relative_path) for url, relative_path in requests]


def install_capture_tree(staging_dir: Path, destination: Path) -> None:
    """Swap in a complete capture only after every requested response succeeded."""
    if not staging_dir.is_dir():
        raise FileNotFoundError(f"capture staging directory is missing: {staging_dir}")

    backup = destination.with_name(f".{destination.name}.previous")
    if backup.exists():
        if destination.exists():
            shutil.rmtree(backup)
        else:
            backup.rename(destination)
    if destination.exists():
        destination.rename(backup)
    try:
        staging_dir.rename(destination)
    except BaseException:
        if backup.exists() and not destination.exists():
            backup.rename(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-suitability", action="store_true")
    parser.add_argument(
        "--district-code",
        action="append",
        dest="district_codes",
        metavar="BBS_CODE",
        help="capture suitability only for this district; repeat to select several (default: all districts)",
    )
    args = parser.parse_args()

    if args.skip_suitability and args.district_codes:
        parser.error("--district-code cannot be combined with --skip-suitability")

    with tempfile.TemporaryDirectory(prefix=".barc-capture-", dir=CAPTURE_DIR.parent) as temp_dir:
        staging_dir = Path(temp_dir) / CAPTURE_DIR.name
        staging_dir.mkdir()
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=False) as client:
            capture = Capturer(client, staging_dir)
            capture.get_many([
                (f"{PORTAL}/copyrightPolicy", "portal/copyright_policy.html"),
                (f"{PORTAL}/api/crops-all-info", "portal/crops_all_info.json"),
                *[
                    (f"{PORTAL}/api/crop/get-prod-tech/{crop_id}", f"portal/prod_tech_{crop_id}.json")
                    for crop_id in PORTAL_PROD_TECH_CROPS
                ],
            ])
            variety_details: list[tuple[str, str]] = []
            for crop_id in PORTAL_VARIETY_LIST_CROPS:
                body = capture.get(
                    f"{PORTAL}/api/get-variety-names-by-crop/{crop_id}",
                    f"portal/variety_names_{crop_id}.json",
                )
                if crop_id in PORTAL_VARIETY_DETAIL_CROPS:
                    for variety in json.loads(body):
                        variety_id = int(variety["id"])
                        variety_details.append((
                            f"{PORTAL}/api/get-variety-by-id/{variety_id}",
                            f"portal/variety/{variety_id}.json",
                        ))
            capture.get_many(variety_details)
            districts = json.loads(capture.get(
                f"{SUITABILITY_API}/api/crop-suitability-districts", "suitability/districts.json"
            ))
            selected_districts = select_suitability_districts(
                districts, set(args.district_codes) if args.district_codes else None
            )
            selected_codes = {str(int(item["district_c"])) for item in selected_districts}
            upazila_lists = capture.get_many([
                (
                    f"{SUITABILITY_API}/api/crop-suitability-upazilas/{int(district['district_c'])}",
                    f"suitability/upazilas_{int(district['district_c'])}.json",
                )
                for district in districts
            ])
            suitability_requests = []
            for district, upazila_body in zip(districts, upazila_lists, strict=True):
                code = str(int(district["district_c"]))
                upazilas = json.loads(upazila_body)
                if args.skip_suitability or code not in selected_codes:
                    continue
                print(
                    f"Capturing {len(upazilas)} upazila suitability records "
                    f"for {district['district_n']} ({code})",
                    flush=True,
                )
                for upazila in upazilas:
                    upazila_code = str(int(upazila["upazila_code"]))
                    suitability_requests.append((
                        f"{SUITABILITY_API}/api/crop-suitability/{upazila_code}",
                        f"suitability/upazila/{upazila_code}.json",
                    ))
            capture.get_many(suitability_requests)

        manifest = {
            "manifest_version": 1,
            "publisher": "Bangladesh Agricultural Research Council (BARC)",
            "captured_by": "backend/scripts/capture_barc_portal_sources.py",
            "files": sorted(capture.entries, key=lambda entry: entry["path"]),
        }
        (staging_dir / "capture_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        install_capture_tree(staging_dir, CAPTURE_DIR)
    print(f"Captured {len(capture.entries)} public responses into {CAPTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
