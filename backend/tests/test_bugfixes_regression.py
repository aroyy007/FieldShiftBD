"""Regression tests for the 12 bugs fixed in the cross-check pass.

Each test pins one fix so future refactors can't silently break it.
"""

from datetime import date
from decimal import Decimal

import pytest


# ── Bug 1: chat_engine factor extraction ─────────────────────────────────────
def test_chat_engine_handles_agricultural_knowledge_without_factor_key(
    client_and_farm, monkeypatch
):
    """Bug 1 — knowledge record missing 'factor' key in content dict used to 500.

    The fix reads r.content.get('factor') with a safe fallback to r.category
    instead of touching a non-existent r.factor attribute.
    """
    from app.models.core import AgriculturalKnowledge
    from sqlalchemy.orm import Session
    from app.core.database import get_db

    # Pull a Session from the running app's dependency overrides
    db: Session = next(iter(client_and_farm[0].app.dependency_overrides[get_db]()))

    # Need a crop to attach knowledge to
    from app.models.core import Crop
    crop = db.query(Crop).first()
    db.add(
        AgriculturalKnowledge(
            crop_id=crop.id,
            category="irrigation",
            content={"schedule": "every 3 days"},  # no 'factor' key
            source_name="test-fixture",
            review_status="approved",
        )
    )
    db.commit()

    client, farmland_id, _, _ = client_and_farm
    res = client.post(f"/farmlands/{farmland_id}/chat", json={"message": "irrigation help"})
    assert res.status_code == 200
    assert "assistant_message" in res.json()


# ── Bug 2: M5 title auto-rename only on placeholder titles ───────────────────
def test_message_to_named_conversation_does_not_overwrite_title(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    res = client.post(
        f"/farmlands/{farmland_id}/conversations",
        json={"title": "Custom Title"},
    )
    conv_id = res.json()["id"]
    client.post(
        f"/farmlands/{farmland_id}/conversations/{conv_id}/messages",
        json={"message": "hello world this should not rename"},
    )
    res = client.get(f"/farmlands/{farmland_id}/conversations/{conv_id}")
    assert res.json()["title"] == "Custom Title"


def test_message_to_default_conversation_renames_to_message(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    res = client.post(
        f"/farmlands/{farmland_id}/conversations",
        json={"title": "New conversation"},
    )
    conv_id = res.json()["id"]
    client.post(
        f"/farmlands/{farmland_id}/conversations/{conv_id}/messages",
        json={"message": "rice planting"},
    )
    res = client.get(f"/farmlands/{farmland_id}/conversations/{conv_id}")
    assert res.json()["title"] == "rice planting"


# ── Bug 3: register race condition ────────────────────────────────────────────
def test_register_returns_409_for_duplicate_phone(client_and_farm):
    client, _, _, _ = client_and_farm
    # Test farmer already exists with +8801700000000 from the fixture
    res = client.post(
        "/auth/register",
        json={"name": "Dup", "phone_e164": "+8801700000000"},
    )
    assert res.status_code == 409


def test_register_creates_farmer_with_normalized_phone(client_and_farm):
    """Bug 3+11 — register must successfully create a FarmerProfile even with
    visual separators in the phone input, and must not 409 on a fresh number."""
    client, _, _, _ = client_and_farm
    unique_phone = "+8801712345000"
    res = client.post(
        "/auth/register",
        json={"name": "Fresh Farmer", "phone_e164": "+880 1712-345 000"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["access_token"]
    assert "farmer_id" in body


def test_register_normalizes_phone_with_spaces_and_dashes():
    """Bug 11 — phone validator now strips visual separators and accepts common formats."""
    from app.schemas.profile import FarmerRegisterRequest

    req = FarmerRegisterRequest(name="x", phone_e164="+880 1712-345 678")
    assert req.phone_e164 == "+8801712345678"

    req = FarmerRegisterRequest(name="x", phone_e164="  +8801712345678  ")
    assert req.phone_e164 == "+8801712345678"

    # Too short still rejected
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        FarmerRegisterRequest(name="x", phone_e164="+880")


# ── Bug 4: select_crop refuses to pile up planned seasons ────────────────────
def test_select_crop_blocks_when_planned_season_already_exists(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    # The fixture pre-creates an 'active' season; verify a second 'planned'
    # is rejected with 409.
    from app.services.m2_advisor import select_crop
    from app.core.database import get_db
    from app.models.core import Crop

    db = next(iter(client_and_farm[0].app.dependency_overrides[get_db]()))
    crop = db.query(Crop).first()
    from app.services.m2_advisor import M2ConflictError

    with pytest.raises(M2ConflictError):
        select_crop(
            db=db,
            farmland_id=farmland_id,
            farmer_id=None,
            crop_id=crop.id,
            crop_variety_id=None,
            variety_name=None,
            recommendation_id=None,
            planting_date=date(2027, 1, 1),
            expected_harvest_date=date(2027, 4, 1),
            budget_amount=Decimal("1000"),
            budget_currency="BDT",
        )


# ── Bug 5: SECRET_KEY example is now empty / fail-closed ─────────────────────
def test_env_example_does_not_contain_real_secret_key():
    """The committed .env.example must not contain a hardcoded secret."""
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, ".env.example")
    with open(path) as f:
        content = f.read()
    # The old hardcoded value was 64 hex chars
    assert "414b93c040a4da207299009f6e26eddda44f8010e79ad1c6080c42b34bab9eaa" not in content
    # And the SECRET_KEY line itself should be blank or have no value
    for line in content.splitlines():
        if line.startswith("SECRET_KEY="):
            value = line.split("=", 1)[1].strip()
            assert value == "", f"SECRET_KEY must be empty, got {value!r}"


# ── Bug 7: GET-by-id endpoints for tasks and problems ─────────────────────────
def test_get_task_by_id_returns_task(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    res = client.post(
        f"/farmlands/{farmland_id}/tasks",
        json={"title": "Water the field", "priority": "normal"},
    )
    assert res.status_code == 201
    task_id = res.json()["id"]

    res = client.get(f"/farmlands/{farmland_id}/tasks/{task_id}")
    assert res.status_code == 200
    assert res.json()["id"] == task_id
    assert res.json()["title"] == "Water the field"


def test_get_task_by_id_404_when_missing(client_and_farm):
    import uuid
    client, farmland_id, _, _ = client_and_farm
    res = client.get(f"/farmlands/{farmland_id}/tasks/{uuid.uuid4()}")
    assert res.status_code == 404


def test_get_problem_by_id_returns_problem(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    res = client.post(
        f"/farmlands/{farmland_id}/problems",
        json={"category": "pest", "description": "Aphids on leaves", "severity": "low"},
    )
    assert res.status_code == 201
    problem_id = res.json()["id"]

    res = client.get(f"/farmlands/{farmland_id}/problems/{problem_id}")
    assert res.status_code == 200
    assert res.json()["id"] == problem_id


# ── Bug 8: onboarding completion timestamp gets stamped ──────────────────────
def test_onboarding_status_stamps_completed_at_on_first_full_pass(client_and_farm):
    from app.core.database import get_db
    from app.models.profile import FarmerProfile
    from app.models.core import Farmer

    client, farmland_id, _, _ = client_and_farm
    db = next(iter(client_and_farm[0].app.dependency_overrides[get_db]()))
    farmer = db.query(Farmer).first()

    # Ensure a FarmerProfile exists (it normally does after /auth/register,
    # but the bare fixture only has a Farmer). Create it directly to mirror
    # the post-registration state.
    profile = db.query(FarmerProfile).filter_by(farmer_id=farmer.id).first()
    if profile is None:
        profile = FarmerProfile(farmer_id=farmer.id)
        db.add(profile)
        db.commit()
    assert profile.onboarding_completed_at is None

    # Fill every required field
    res = client.patch(
        f"/farmlands/{farmland_id}",
        json={
            "division": "Dhaka",
            "district": "Gazipur",
            "upazila": "Kaliakair",
            "land_type": "medium_high",
            "latitude": 24.0,
            "longitude": 90.4,
            "soil_type": "loam",
            "irrigation_available": True,
            "water_source": "tube well",
            "farming_method": "mixed",
            "budget_amount": 10000,
            "previous_crop": "rice",
            "previous_yield_amount": 500,
        },
    )
    assert res.status_code == 200, res.text
    res = client.patch(
        "/profile/farmer-profile",
        json={
            "farming_experience_years": 5,
            "equipment": ["tractor"],
            "livestock": ["cow"],
        },
    )
    assert res.status_code == 200, res.text
    res = client.get(f"/farmlands/{farmland_id}/onboarding-status")
    assert res.status_code == 200
    assert res.json()["is_complete"] is True

    db.expire_all()
    db.refresh(profile)
    assert profile.onboarding_completed_at is not None


# ── Bug 11: phone validator accepts spaced/dashed formats ────────────────────
def test_phone_validator_accepts_international_lengths():
    from app.schemas.profile import FarmerRegisterRequest

    # Standard E.164
    req = FarmerRegisterRequest(name="x", phone_e164="+8801712345678")
    assert req.phone_e164 == "+8801712345678"

    # US 11-digit
    req = FarmerRegisterRequest(name="x", phone_e164="+14155552671")
    assert req.phone_e164 == "+14155552671"

    # With parentheses around area code
    req = FarmerRegisterRequest(name="x", phone_e164="+1(415)555-2671")
    assert req.phone_e164 == "+14155552671"


def test_phone_validator_rejects_bad_inputs():
    from app.schemas.profile import FarmerRegisterRequest
    import pydantic

    # No plus prefix
    with pytest.raises(pydantic.ValidationError):
        FarmerRegisterRequest(name="x", phone_e164="8801712345678")

    # Non-digit
    with pytest.raises(pydantic.ValidationError):
        FarmerRegisterRequest(name="x", phone_e164="+88abc")


# ── Bug 12: chat_engine rolls back on failure so next request is clean ───────
def test_chat_engine_does_not_leak_aborted_session(client_and_farm, monkeypatch):
    """If generation blows up mid-call, the next chat must still succeed.

    Regression: the engine used to leave the session in an aborted state, so
    every subsequent call also returned 500. The fix wraps the body in
    try/except + db.rollback() so the next request starts clean.
    """
    from app.services import chat_engine
    from app.core.database import get_db

    state = {"fail": True}

    def boom(*args, **kwargs):
        if state["fail"]:
            raise RuntimeError("simulated failure")
        return None

    monkeypatch.setattr(chat_engine, "generate_gemini_reply", boom)

    client, farmland_id, _, _ = client_and_farm

    # First call: boom — should return 500 (or whatever the framework maps to)
    with pytest.raises(RuntimeError):
        client.post(f"/farmlands/{farmland_id}/chat", json={"message": "test 1"})

    # Second call: should succeed because rollback cleaned up the session
    state["fail"] = False
    res = client.post(f"/farmlands/{farmland_id}/chat", json={"message": "test 2"})
    assert res.status_code == 200
    assert res.json()["assistant_message"]["message"]  # non-empty fallback reply
