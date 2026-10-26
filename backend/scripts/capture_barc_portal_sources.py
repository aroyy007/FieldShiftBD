"""Capture the public BARC crop-zoning JSON responses used by M1 and M2.

The Agri-Advisory Portal (portal.cropzoning.gov.bd) and its suitability API
(api1.cropzoning.gov.bd) are called anonymously by BARC's own public pages.
This script requests only those documented public routes, rate-limits every
request, and writes each response byte-for-byte with its SHA-256 digest. It
never logs in, sends credentials, or calls role-gated CZIS/GeoServer services.

Run from ``backend`` (network access required; the app never does this at
runtime):

    python -m scripts.capture_barc_portal_sources

Captured files are inputs to ``python -m scripts.import_reference_data``. Re-run
the capture to refresh the evidence before the 180-day policy window expires,
then review the claim manifest against the refreshed text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime
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

# Portal crop ids (from /api/crops-all-info) for the crops in the M1 catalog.
PORTAL_PROD_TECH_CROPS = (36, 4, 5, 3)
PORTAL_VARIETY_LIST_CROPS = (36, 4, 5, 3, 2)
# Variety details are captured for crops whose M2 harvest records use them.
PORTAL_VARIETY_DETAIL_CROPS = (36, 4, 5)
# BBS district geocodes whose upazila suitability tables are captured.
SUITABILITY_DISTRICTS = ("2019", "3033", "3026", "4561", "5081")


class Capturer:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client
        self.entries: list[dict] = []

    def get(self, url: str, relative_path: str) -> bytes:
        time.sleep(REQUEST_INTERVAL_SECONDS)
        response = self.client.get(url)
        response.raise_for_status()
        body = response.content
        target = CAPTURE_DIR / relative_path
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-suitability", action="store_true")
    args = parser.parse_args()

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=False) as client:
        capture = Capturer(client)
        capture.get(f"{PORTAL}/copyrightPolicy", "portal/copyright_policy.html")
        capture.get(f"{PORTAL}/api/crops-all-info", "portal/crops_all_info.json")
        for crop_id in PORTAL_PROD_TECH_CROPS:
            capture.get(f"{PORTAL}/api/crop/get-prod-tech/{crop_id}", f"portal/prod_tech_{crop_id}.json")
        for crop_id in PORTAL_VARIETY_LIST_CROPS:
            body = capture.get(
                f"{PORTAL}/api/get-variety-names-by-crop/{crop_id}",
                f"portal/variety_names_{crop_id}.json",
            )
            if crop_id in PORTAL_VARIETY_DETAIL_CROPS:
                for variety in json.loads(body):
                    capture.get(
                        f"{PORTAL}/api/get-variety-by-id/{int(variety['id'])}",
                        f"portal/variety/{int(variety['id'])}.json",
                    )
        districts = json.loads(capture.get(
            f"{SUITABILITY_API}/api/crop-suitability-districts", "suitability/districts.json"
        ))
        for district in districts:
            code = str(int(district["district_c"]))
            upazilas = json.loads(capture.get(
                f"{SUITABILITY_API}/api/crop-suitability-upazilas/{code}",
                f"suitability/upazilas_{code}.json",
            ))
            if args.skip_suitability or code not in SUITABILITY_DISTRICTS:
                continue
            for upazila in upazilas:
                upazila_code = str(int(upazila["upazila_code"]))
                capture.get(
                    f"{SUITABILITY_API}/api/crop-suitability/{upazila_code}",
                    f"suitability/upazila/{upazila_code}.json",
                )

    manifest = {
        "manifest_version": 1,
        "publisher": "Bangladesh Agricultural Research Council (BARC)",
        "captured_by": "backend/scripts/capture_barc_portal_sources.py",
        "files": sorted(capture.entries, key=lambda entry: entry["path"]),
    }
    (CAPTURE_DIR / "capture_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Captured {len(capture.entries)} public responses into {CAPTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
