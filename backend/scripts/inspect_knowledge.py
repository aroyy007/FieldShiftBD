"""Inspect M2 agricultural knowledge rows and why a season plan may be unavailable.

Run: python scripts/inspect_knowledge.py
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.core import AgriculturalKnowledge, Crop  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        print("== knowledge rows by crop / review_status / category ==")
        rows = db.execute(
            select(
                Crop.name,
                AgriculturalKnowledge.review_status,
                AgriculturalKnowledge.category,
                func.count(AgriculturalKnowledge.id),
            )
            .join(Crop, Crop.id == AgriculturalKnowledge.crop_id)
            .group_by(
                Crop.name,
                AgriculturalKnowledge.review_status,
                AgriculturalKnowledge.category,
            )
            .order_by(Crop.name, AgriculturalKnowledge.review_status)
        ).all()
        for name, status, category, count in rows:
            print(f"  {str(name):12} {str(status):16} {str(category):26} {count}")

        print("\n== review_status totals ==")
        for status, count in db.execute(
            select(
                AgriculturalKnowledge.review_status, func.count(AgriculturalKnowledge.id)
            ).group_by(AgriculturalKnowledge.review_status)
        ).all():
            print(f"  {status}: {count}")

        print("\n== sample Potato rows (approved first) ==")
        potato = db.scalar(select(Crop).where(Crop.name == "Potato"))
        if potato is None:
            print("  no Potato crop row")
            return
        for row in db.execute(
            select(
                AgriculturalKnowledge.id,
                AgriculturalKnowledge.review_status,
                AgriculturalKnowledge.category,
                AgriculturalKnowledge.region_code,
                AgriculturalKnowledge.source_name,
            )
            .where(AgriculturalKnowledge.crop_id == potato.id)
            .order_by(AgriculturalKnowledge.review_status)
            .limit(12)
        ).all():
            print(f"  {row[0]} status={row[1]:12} cat={row[2]:26} region={row[3]} src={row[4]}")


if __name__ == "__main__":
    main()
