"""Import the M1 crop catalog and all policy-accepted M2 knowledge in one step.

Run from ``backend`` after ``alembic upgrade head``:

    python -m scripts.import_reference_data --check-only   # validate, no DB writes
    python -m scripts.import_reference_data                # import (idempotent)

Order: M1 crops and varieties -> legacy BARC Potato/Comilla snapshot -> BARC
portal claims, variety durations, and upazila regional context -> the
review-gated source-grounding notes (kept ``in_review``). Everything runs in
one transaction except the source-grounding notes, which use their existing
importer. Re-running the command changes nothing unless a source capture,
claim, or catalog entry changed. Existing rows owned by people or other
policies are never overwritten; they are listed as conflicts, and the command
exits with status 3 so the conflict is not silently ignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

SNAPSHOT_PATH = BACKEND_DIR / "app" / "data" / "m2_knowledge_sources" / "barc_potato_comilla_snapshot.json"


def _today() -> date:
    return datetime.now(ZoneInfo("Asia/Dhaka")).date()


def check_only(evaluated_on: date) -> int:
    from app.services.m1_reference import crop_catalog, geography
    from app.services.m2_portal_policy import (
        build_bilingual_content,
        build_regional_content,
        PortalPolicyError,
        build_variety_content,
        claims_manifest,
    )
    from app.services.m2_source_policy import validate_barc_upazila_snapshot
    from app.services.source_captures import capture_manifest, read_verified_bytes, read_verified_json

    for path in capture_manifest():
        read_verified_bytes(path)
    geo = geography()
    for claim in claims_manifest()["claims"]:
        build_bilingual_content(claim, evaluated_on)
    varieties = 0
    variety_rejections: list[str] = []
    for crop in crop_catalog()["crops"]:
        if crop["key"] not in claims_manifest()["variety_duration"]["crops"]:
            continue
        for portal_crop_id in crop["portal_crop_ids"]:
            for item in read_verified_json(f"portal/variety_names_{portal_crop_id}.json"):
                try:
                    build_variety_content(crop["key"], int(item["id"]), evaluated_on)
                    varieties += 1
                except PortalPolicyError as error:
                    variety_rejections.append(f"{crop['key']}: {error}")
    regional = 0
    for path in capture_manifest():
        if path.startswith("suitability/upazila/"):
            code = path.split("/")[-1].removesuffix(".json")
            for crop in crop_catalog()["crops"]:
                regional += build_regional_content(crop["key"], code, evaluated_on) is not None
    for line in variety_rejections:
        print(f"  rejected: {line}")
    snapshot_ok = True
    try:
        validate_barc_upazila_snapshot(json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")), evaluated_on=evaluated_on)
    except ValueError as error:
        snapshot_ok = False
        print(f"Legacy BARC snapshot not accepted on {evaluated_on}: {error}")
    print(
        f"Validated {len(capture_manifest())} pinned captures, {len(geo.districts)} districts / "
        f"{len(geo.upazilas)} upazilas, {len(claims_manifest()['claims'])} bilingual claims, "
        f"{varieties} variety durations, {regional} regional context records; legacy snapshot "
        f"{'accepted' if snapshot_ok else 'rejected'}. No database connection opened."
    )
    return 0


def run_import(evaluated_on: date) -> int:
    from app.core.database import SessionLocal
    from app.services.m1_catalog_import import import_crop_catalog
    from app.services.m2_source_import import (
        M2CropCatalogDependencyError,
        M2SourceImportConflict,
        import_barc_snapshot,
        import_portal_knowledge,
    )
    from app.services.m2_source_policy import SourcePolicyError
    from scripts.import_agricultural_knowledge import DEFAULT_DATA_PATH, import_records, validate_dataset

    with SessionLocal() as db:
        try:
            catalog = import_crop_catalog(db)
            legacy = "skipped"
            legacy_conflicts: list[str] = []
            try:
                record, created = import_barc_snapshot(
                    db,
                    json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")),
                    evaluated_on=evaluated_on,
                    crop_id=catalog.crop_ids.get("potato"),
                )
                changed = db.is_modified(record)  # must be read before the flush
                db.flush()
                legacy = "created" if created else ("refreshed" if changed else "unchanged")
            except M2SourceImportConflict as error:
                legacy = "conflict (left unchanged)"
                legacy_conflicts.append(f"legacy BARC snapshot: {error}")
            except (M2CropCatalogDependencyError, SourcePolicyError) as error:
                legacy = f"not imported: {error}"
            knowledge = import_portal_knowledge(db, catalog.crop_ids, evaluated_on=evaluated_on)
            db.commit()
        except Exception:
            db.rollback()
            raise

    notes = import_records(validate_dataset(DEFAULT_DATA_PATH))
    print("M1 crop catalog:")
    print(
        f"  crops created={catalog.crops_created} updated={catalog.crops_updated} "
        f"unchanged={catalog.crops_unchanged} preserved_existing={catalog.crops_preserved}"
    )
    print(
        f"  varieties created={catalog.varieties_created} updated={catalog.varieties_updated} "
        f"unchanged={catalog.varieties_unchanged} preserved_existing={catalog.varieties_preserved}"
    )
    for note in catalog.notes:
        print(f"  note: {note}")
    print(f"Legacy BARC Potato/Comilla snapshot: {legacy}")
    print(
        f"M2 portal knowledge: created={knowledge.created} refreshed={knowledge.refreshed} "
        f"unchanged={knowledge.unchanged} by_policy={knowledge.by_policy}"
    )
    for line in knowledge.rejected:
        print(f"  rejected: {line}")
    print(f"Source-grounding notes (in_review): inserted={notes[0]} changed={notes[1]} unchanged={notes[2]}")
    conflicts = catalog.conflicts + legacy_conflicts + knowledge.conflicts
    for conflict in conflicts:
        print(f"CONFLICT: {conflict}")
    return 3 if conflicts else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check-only", action="store_true", help="validate data without a database")
    parser.add_argument("--evaluated-on", type=date.fromisoformat, default=None, help="policy evaluation date (default: today in Asia/Dhaka)")
    args = parser.parse_args()
    evaluated_on = args.evaluated_on or _today()
    return check_only(evaluated_on) if args.check_only else run_import(evaluated_on)


if __name__ == "__main__":
    raise SystemExit(main())
