"""Validate and import review-gated agricultural knowledge seed records.

Run from the backend directory:
    python -m scripts.import_agricultural_knowledge --check-only
    python -m scripts.import_agricultural_knowledge

New records are always seeded as ``in_review``. Re-imports preserve a review
decision when the source record is unchanged and return changed records to
``in_review`` so a reviewed version cannot silently survive changed content.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = (
    BACKEND_DIR / "app" / "data" / "agricultural_knowledge_seed.json"
)
sys.path.insert(0, str(BACKEND_DIR))


REQUIRED_RECORD_FIELDS = {
    "key",
    "category",
    "region_code",
    "source_name",
    "source_reference",
    "effective_from",
    "effective_to",
    "review_status",
    "content",
}
REVIEWABLE_STATUSES = {"in_review"}
UPDATE_FIELDS = (
    "crop_id",
    "crop_variety_id",
    "category",
    "region_code",
    "content",
    "source_name",
    "source_reference",
    "effective_from",
    "effective_to",
)


def _optional_date(value: Any, field_name: str, record_key: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{record_key}: {field_name} must be an ISO date or null")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{record_key}: invalid {field_name}: {value!r}") from exc


def _optional_uuid(value: Any, field_name: str, record_key: str) -> UUID | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{record_key}: {field_name} must be a UUID string or null")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(
            f"{record_key}: invalid UUID for {field_name}: {value!r}"
        ) from exc


def validate_dataset(path: Path) -> list[dict[str, Any]]:
    """Load and validate data without importing DB settings or opening a DB."""
    with path.open(encoding="utf-8") as source_file:
        dataset = json.load(source_file)

    if (
        not isinstance(dataset, dict)
        or dataset.get("schema_version") != 1
        or dataset.get("default_review_status") != "in_review"
    ):
        raise ValueError(
            "Seed file must use schema_version 1 and default_review_status in_review"
        )
    records = dataset.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Seed file must contain a non-empty records array")

    seen_keys: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"records[{index}] must be an object")
        missing = REQUIRED_RECORD_FIELDS - record.keys()
        if missing:
            raise ValueError(f"records[{index}] missing fields: {', '.join(sorted(missing))}")

        key = record["key"]
        if not isinstance(key, str) or not key or key in seen_keys:
            raise ValueError(f"records[{index}] has an empty or duplicate key")
        seen_keys.add(key)

        if (
            not isinstance(record["category"], str)
            or not 1 <= len(record["category"]) <= 80
        ):
            raise ValueError(f"{key}: category must contain 1 to 80 characters")
        if (
            not isinstance(record["source_name"], str)
            or not 1 <= len(record["source_name"]) <= 200
        ):
            raise ValueError(
                f"{key}: source_name must contain 1 to 200 characters"
            )
        if (
            not isinstance(record["source_reference"], str)
            or not record["source_reference"].startswith("https://")
        ):
            raise ValueError(f"{key}: source_reference must be an HTTPS URL")
        if record["region_code"] not in (None, "BD"):
            raise ValueError(
                f"{key}: use null or the agreed Bangladesh ISO code 'BD'"
            )
        if (
            not isinstance(record["review_status"], str)
            or record["review_status"] not in REVIEWABLE_STATUSES
        ):
            raise ValueError(f"{key}: seed data cannot approve or reject records")
        if not isinstance(record["content"], dict):
            raise ValueError(f"{key}: content must be a JSON object")
        if record["content"].get("farmer_facing") is not False:
            raise ValueError(
                f"{key}: source-grounding seed records must not be farmer-facing"
            )
        source_claims = record["content"].get("source_claims")
        if not isinstance(source_claims, list) or not source_claims:
            raise ValueError(f"{key}: content must include source_claims")
        for claim in source_claims:
            evidence = claim.get("evidence") if isinstance(claim, dict) else None
            if not isinstance(evidence, list) or not evidence:
                raise ValueError(f"{key}: every source claim needs evidence")
            for source in evidence:
                if (
                    not isinstance(source, dict)
                    or not isinstance(source.get("url"), str)
                    or not source["url"].startswith("https://")
                    or not isinstance(source.get("accessed_on"), str)
                ):
                    raise ValueError(
                        f"{key}: evidence requires an HTTPS URL and accessed_on date"
                    )
                _optional_date(source["accessed_on"], "evidence.accessed_on", key)
        start = _optional_date(record["effective_from"], "effective_from", key)
        end = _optional_date(record["effective_to"], "effective_to", key)
        _optional_uuid(record.get("crop_id"), "crop_id", key)
        _optional_uuid(record.get("crop_variety_id"), "crop_variety_id", key)
        if start is not None and end is not None and end < start:
            raise ValueError(
                f"{key}: effective_to cannot be earlier than effective_from"
            )

    return records


def stable_id(record_key: str) -> UUID:
    """Return an idempotent UUID for a stable seed key."""
    return uuid5(
        NAMESPACE_URL,
        f"https://fieldshiftbd.local/agricultural-knowledge/{record_key}",
    )


def import_records(records: list[dict[str, Any]]) -> tuple[int, int, int]:
    # Delayed imports allow --check-only to work without a DATABASE_URL.
    from app.core.database import SessionLocal
    from app.models.core import AgriculturalKnowledge

    inserted = refreshed = unchanged = 0
    with SessionLocal() as db:
        try:
            for record in records:
                row_id = stable_id(record["key"])
                values = {field: record.get(field) for field in UPDATE_FIELDS}
                values["crop_id"] = _optional_uuid(
                    record.get("crop_id"), "crop_id", record["key"]
                )
                values["crop_variety_id"] = _optional_uuid(
                    record.get("crop_variety_id"), "crop_variety_id", record["key"]
                )
                values["effective_from"] = _optional_date(
                    record["effective_from"], "effective_from", record["key"]
                )
                values["effective_to"] = _optional_date(
                    record["effective_to"], "effective_to", record["key"]
                )
                current = db.get(AgriculturalKnowledge, row_id)

                if current is None:
                    db.add(
                        AgriculturalKnowledge(
                            id=row_id,
                            **values,
                            review_status=record["review_status"],
                            reviewed_by=None,
                            reviewed_at=None,
                        )
                    )
                    inserted += 1
                    continue

                changed = any(
                    getattr(current, field) != value
                    for field, value in values.items()
                )
                if not changed:
                    unchanged += 1
                    continue

                for field, value in values.items():
                    setattr(current, field, value)
                current.review_status = "in_review"
                current.reviewed_by = None
                current.reviewed_at = None
                refreshed += 1

            db.commit()
        except Exception:
            db.rollback()
            raise

    return inserted, refreshed, unchanged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="JSON seed file (defaults to app/data/agricultural_knowledge_seed.json)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate the JSON without connecting to PostgreSQL",
    )
    args = parser.parse_args()

    records = validate_dataset(args.data)
    if args.check_only:
        print(
            f"Validated {len(records)} knowledge records in {args.data}; "
            "no database connection opened."
        )
        return 0

    inserted, refreshed, unchanged = import_records(records)
    print(
        "Knowledge import complete: "
        f"{inserted} inserted, {refreshed} changed and returned to in_review, "
        f"{unchanged} unchanged. Records absent from the seed were not deleted."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Knowledge import failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
