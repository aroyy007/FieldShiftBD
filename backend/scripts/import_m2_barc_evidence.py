"""Import the validated BARC Potato/Comilla snapshot after M1 seeds the crop catalog.

Run from ``backend`` with:
    python -m scripts.import_m2_barc_evidence
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.database import SessionLocal
from app.services.m2_source_import import import_barc_snapshot


SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "data"
    / "m2_knowledge_sources"
    / "barc_potato_comilla_snapshot.json"
)
FARM_TIMEZONE = ZoneInfo("Asia/Dhaka")


def main() -> None:
    with SNAPSHOT_PATH.open(encoding="utf-8") as source_file:
        snapshot = json.load(source_file)
    with SessionLocal() as db:
        record, created = import_barc_snapshot(
            db, snapshot, evaluated_on=datetime.now(FARM_TIMEZONE).date()
        )
        db.commit()
        print(
            f"{'Imported' if created else 'Refreshed'} M2 source-policy record "
            f"{record.id} for Potato / Comilla upazila; review_status={record.review_status}, "
            "acceptance=automated_source_validation."
        )


if __name__ == "__main__":
    main()
