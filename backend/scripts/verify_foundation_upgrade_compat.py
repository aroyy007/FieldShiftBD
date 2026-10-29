"""Exercise the new migration against a baseline database with legacy rows.

This intentionally downgrades and upgrades the configured database. It refuses
to run unless DATABASE_URL is PostgreSQL and its database name contains
``test``. Use only a disposable integration database.
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.models import Crop, Farmer, Farmland


def main() -> None:
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql" or "test" not in (url.database or "").lower():
        raise SystemExit("Refusing destructive migration verification outside a PostgreSQL test database")

    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        current = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    if current != "c6f4e739a2b1":
        raise SystemExit(f"Expected the verified foundation head before compatibility test; found {current}")

    command.downgrade(alembic_config, "b904f5e0c3aa")
    token = uuid4().hex[:9]
    phone = f"+8801{token[:9]}"
    crop_name = f"SYNTHETIC LEGACY TEST ONLY {token}"
    farm_name = f"SYNTHETIC LEGACY TEST ONLY {token}"
    with Session(engine) as session:
        farmer = Farmer(name="SYNTHETIC LEGACY TEST ONLY", phone_e164=phone)
        crop = Crop(name=crop_name)
        session.add_all([farmer, crop])
        session.flush()
        farmland = Farmland(
            farmer_id=farmer.id,
            name=farm_name,
            land_area_sqm=1000,
            land_area_display_unit="square_metre",
        )
        session.add(farmland)
        session.commit()
        farmer_id, farmland_id = farmer.id, farmland.id

    command.upgrade(alembic_config, "head")
    with Session(engine) as session:
        preserved = session.scalar(
            select(Farmland).where(Farmland.id == farmland_id, Farmland.farmer_id == farmer_id)
        )
        assert preserved is not None and preserved.name == farm_name
        assert session.get(Farmer, farmer_id).phone_e164 == phone
        assert session.scalar(select(Crop.id).where(Crop.name == crop_name)) is not None
    engine.dispose()
    print("Foundation migration preserved synthetic pre-existing farmer, farm, and crop rows.")


if __name__ == "__main__":
    main()
