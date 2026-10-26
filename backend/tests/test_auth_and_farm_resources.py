"""Integration coverage for password auth and per-farm resources."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select


def test_password_is_required_hashed_and_verified(client_and_farm):
    client, _, _, _ = client_and_farm
    password = "grain harvest secure phrase 42"
    registration = client.post(
        "/auth/register",
        json={"name": "Password farmer", "phone_e164": "+8801712345999", "password": password},
    )
    assert registration.status_code == 201, registration.text

    from app.core.database import get_db
    from app.models.core import Farmer

    db = next(iter(client.app.dependency_overrides[get_db]()))
    farmer = db.scalar(select(Farmer).where(Farmer.phone_e164 == "+8801712345999"))
    assert farmer is not None
    assert farmer.password_hash and farmer.password_hash.startswith("$argon2id$")
    assert farmer.password_hash != password
    assert password not in registration.text

    valid = client.post("/auth/login", json={"phone_e164": "+8801712345999", "password": password})
    assert valid.status_code == 200
    assert valid.json()["access_token"]

    wrong = client.post("/auth/login", json={"phone_e164": "+8801712345999", "password": "wrong password 123"})
    unknown = client.post("/auth/login", json={"phone_e164": "+8801712345888", "password": "wrong password 123"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_auth_rejects_missing_or_too_short_password(client_and_farm):
    client, _, _, _ = client_and_farm
    missing_registration = client.post("/auth/register", json={"name": "No password", "phone_e164": "+8801712345887"})
    short_registration = client.post("/auth/register", json={"name": "Short password", "phone_e164": "+8801712345886", "password": "short"})
    missing_login = client.post("/auth/login", json={"phone_e164": "+8801700000000"})
    assert missing_registration.status_code == 422
    assert short_registration.status_code == 422
    assert missing_login.status_code == 422


def test_farmland_resources_and_village_persist_and_reach_m2_and_chat(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    update = client.patch(
        f"/farmlands/{farmland_id}",
        json={
            "village_or_locality": "  East Village  ",
            "equipment": [" Pump ", "tractor", "pump", ""],
            "budget_amount": "13500.50",
            "budget_currency": "BDT",
            "water_source": "Pond",
            "irrigation_available": True,
            "land_type": "low",
        },
    )
    assert update.status_code == 200, update.text
    saved = update.json()
    assert saved["village_or_locality"] == "East Village"
    assert saved["equipment"] == ["Pump", "tractor"]
    assert saved["budget_amount"] == "13500.50"

    from app.core.database import get_db
    from app.models.core import Farmland
    from app.services.chat_engine import aggregate_farmland_context, build_system_prompt
    from app.services.m2_advisor import profile_from_farmland

    db = next(iter(client.app.dependency_overrides[get_db]()))
    farmland = db.get(Farmland, UUID(str(farmland_id)))
    assert farmland is not None
    m2_profile = profile_from_farmland(db, farmland)
    assert m2_profile.equipment == ["Pump", "tractor"]

    second_farm = Farmland(
        farmer_id=farmland.farmer_id,
        name="Separate resource context",
        land_area_sqm=Decimal("2000"),
        land_area_display_unit="square_metre",
        equipment=["shared pump"],
    )
    db.add(second_farm)
    db.commit()
    prompt = build_system_prompt(aggregate_farmland_context(db, farmland.id, farmland.farmer_id))
    assert "Available Equipment: Pump, tractor" in prompt
    assert "shared pump" not in prompt
    assert "East Village" in prompt
    assert "13500.50" in prompt
