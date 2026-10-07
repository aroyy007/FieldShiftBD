"""Module 1 — Farm Profile & Onboarding API routes.

All farmer registration, authentication, farmland management, and onboarding
progress tracking lives here. This module feeds every other module:

  - Auth (register/login) → unblocks Module 3 and Module 6 (they need farmer identity)
  - Farmland CRUD         → unblocks Module 4 (needs real lat/lon for NASA POWER API)
  - Onboarding status     → unblocks Module 5 (chat drives this question-by-question)
  - Full profile          → unblocks Module 2 (needs soil/water/location for crop advice)

Endpoints:
  POST   /auth/register                           Register a new farmer, get a token
  POST   /auth/login                              Login with phone, get a token
  GET    /profile                                 My full profile (farmer + farmlands)
  PATCH  /profile/farmer-profile                  Update experience, equipment, livestock
  GET    /farmlands                               List my farmlands
  POST   /farmlands                               Create a new farmland
  GET    /farmlands/{farmland_id}                 Get a farmland's full profile
  PATCH  /farmlands/{farmland_id}                 Update any farmland field
  GET    /farmlands/{farmland_id}/onboarding-status  What's filled, what's missing, what to ask next
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.core import Farmland, Farmer
from app.models.profile import FarmerProfile
from app.schemas.profile import (
    FarmlandCreate,
    FarmlandRead,
    FarmlandUpdate,
    FarmerLoginRequest,
    FarmerProfileRead,
    FarmerProfileUpdate,
    FarmerRead,
    FarmerRegisterRequest,
    MyProfileRead,
    OnboardingFieldStatus,
    OnboardingStatusRead,
    TokenResponse,
)

router = APIRouter(tags=["Profile & Onboarding — Module 1"])

# FastAPI dependency aliases — cleaner route signatures
DbSession = Annotated[Session, Depends(get_db)]
CurrentFarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


# ── Onboarding engine ─────────────────────────────────────────────────────────
#
# These two functions define every profile field the onboarding conversation
# needs to collect, in priority order. The first unfilled field becomes the
# next question the chat asks.
#
# Adding a new field to onboarding = add one entry here. Nothing else changes.

def _farmland_onboarding_fields(farmland: Farmland) -> list[tuple[str, str, bool]]:
    """Return (field_name, question_label, is_filled) for each farmland field."""
    return [
        (
            "division",
            "Which division of Bangladesh is your farm located in?",
            bool(farmland.division),
        ),
        (
            "district",
            "Which district is your farm in?",
            bool(farmland.district),
        ),
        (
            "latitude",
            "Can we use your GPS location to get accurate weather for your farm?",
            farmland.latitude is not None,
        ),
        (
            "soil_type",
            "What type of soil does your farmland have? (e.g. clay, loam, sandy)",
            bool(farmland.soil_type),
        ),
        (
            "irrigation_available",
            "Do you have access to irrigation on this land?",
            farmland.irrigation_available is not None,
        ),
        (
            "water_source",
            "What is your main water source? (e.g. river, pond, tube well, rain)",
            bool(farmland.water_source),
        ),
        (
            "farming_method",
            "Do you farm organically, conventionally, or a mix of both?",
            bool(farmland.farming_method),
        ),
        (
            "budget_amount",
            "What is your estimated budget for this crop season (in BDT)?",
            farmland.budget_amount is not None,
        ),
        (
            "previous_crop",
            "What crop did you grow on this land last season?",
            bool(farmland.previous_crop),
        ),
        (
            "previous_yield_amount",
            "How much did you harvest last season, and in what unit? (e.g. 500 kg)",
            farmland.previous_yield_amount is not None,
        ),
    ]


def _profile_onboarding_fields(profile: FarmerProfile | None) -> list[tuple[str, str, bool]]:
    """Return (field_name, question_label, is_filled) for each farmer profile field."""
    if profile is None:
        # Profile doesn't exist yet — all fields are unfilled
        return [
            ("farming_experience_years", "How many years have you been farming?", False),
            ("equipment", "What farming equipment do you own? (e.g. tractor, pump)", False),
            ("livestock", "Do you keep any livestock? If yes, which animals?", False),
        ]
    return [
        (
            "farming_experience_years",
            "How many years have you been farming?",
            profile.farming_experience_years is not None,
        ),
        (
            "equipment",
            "What farming equipment do you own? (e.g. tractor, pump)",
            bool(profile.equipment),  # empty list [] is treated as unfilled
        ),
        (
            "livestock",
            "Do you keep any livestock? If yes, which animals?",
            bool(profile.livestock),  # empty list [] is treated as unfilled
        ),
    ]


def _compute_onboarding_status(
    farmland: Farmland, profile: FarmerProfile | None
) -> OnboardingStatusRead:
    """Calculate the current onboarding completion for a farmland.

    Combines farmland fields + farmer profile fields into a single checklist.
    Calculates percent complete, identifies missing fields, and determines the
    single next question to ask. Used by the chat to drive conversation.
    """
    all_checks = _farmland_onboarding_fields(farmland) + _profile_onboarding_fields(profile)

    fields = [
        OnboardingFieldStatus(field=name, label=label, filled=filled)
        for name, label, filled in all_checks
    ]

    total = len(fields)
    filled_count = sum(1 for f in fields if f.filled)
    percent = round(filled_count * 100 / total) if total > 0 else 0

    missing = [f.field for f in fields if not f.filled]
    next_field = next((f for f in fields if not f.filled), None)

    return OnboardingStatusRead(
        farmland_id=farmland.id,
        percent_complete=percent,
        is_complete=len(missing) == 0,
        missing_fields=missing,
        next_question=next_field.field if next_field else None,
        next_question_label=next_field.label if next_field else None,
        fields=fields,
    )


def _get_owned_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> Farmland:
    """Load a farmland that belongs to the authenticated farmer.

    Raises 404 (not 403) to avoid leaking whether the farmland exists for
    another farmer. A farmer can never see or modify another farmer's data.
    """
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found.")
    return farmland


# ── Auth routes ───────────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer account",
)
def register_farmer(payload: FarmerRegisterRequest, db: DbSession) -> TokenResponse:
    """Register a new farmer with name + phone number.

    - Creates a Farmer row and a linked FarmerProfile row.
    - Returns a JWT token immediately — no separate login step needed.
    - If the phone number is already registered, returns 409.

    The token is valid for 90 days. Store it in the app and send it in every
    future request as: Authorization: Bearer <token>
    """
    existing = db.scalar(
        select(Farmer).where(Farmer.phone_e164 == payload.phone_e164)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this phone number is already registered. Use /auth/login.",
        )

    farmer = Farmer(name=payload.name, phone_e164=payload.phone_e164)
    db.add(farmer)

    # flush() assigns farmer.id so the FarmerProfile FK resolves.
    # Wrap in IntegrityError handling so two parallel registrations with the
    # same phone (race condition) get a clean 409 instead of an unhandled 500.
    try:
        db.flush()
        farmer_profile = FarmerProfile(farmer_id=farmer.id)
        db.add(farmer_profile)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this phone number is already registered. Use /auth/login.",
        )
    db.refresh(farmer)

    token = create_access_token(farmer.id)
    return TokenResponse(access_token=token, farmer_id=farmer.id)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login with phone number",
)
def login_farmer(payload: FarmerLoginRequest, db: DbSession) -> TokenResponse:
    """Login an existing farmer using their phone number.

    Returns a fresh JWT token valid for 90 days.
    Returns 404 if the phone number is not registered.
    """
    farmer = db.scalar(
        select(Farmer).where(Farmer.phone_e164 == payload.phone_e164)
    )
    if farmer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No farmer found with this phone number. Please register first.",
        )

    token = create_access_token(farmer.id)
    return TokenResponse(access_token=token, farmer_id=farmer.id)


# ── Profile routes ────────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=MyProfileRead,
    summary="Get my full profile",
)
def get_my_profile(farmer_id: CurrentFarmerId, db: DbSession) -> MyProfileRead:
    """Return the authenticated farmer's full profile including all farmlands.

    Module 5 (Chat) calls this to inject farmer context into every LLM prompt
    so the assistant answers in a personalized, farm-specific way.
    """
    farmer = db.get(Farmer, farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    profile = db.scalar(
        select(FarmerProfile).where(FarmerProfile.farmer_id == farmer_id)
    )
    farmlands = list(
        db.scalars(select(Farmland).where(Farmland.farmer_id == farmer_id))
    )

    return MyProfileRead(
        farmer=FarmerRead.model_validate(farmer),
        profile=FarmerProfileRead.model_validate(profile) if profile else None,
        farmlands=[FarmlandRead.model_validate(f) for f in farmlands],
    )


@router.patch(
    "/profile/farmer-profile",
    response_model=FarmerProfileRead,
    summary="Update farming experience, equipment, and livestock",
)
def update_farmer_profile(
    payload: FarmerProfileUpdate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
) -> FarmerProfileRead:
    """Update the farmer's extended profile fields.

    Only the fields you send are changed. Everything else stays the same.
    The chat calls this when the farmer answers a profile question like
    "how many years have you been farming?"
    """
    profile = db.scalar(
        select(FarmerProfile).where(FarmerProfile.farmer_id == farmer_id)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Farmer profile not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return FarmerProfileRead.model_validate(profile)


# ── Farmland routes ───────────────────────────────────────────────────────────

@router.get(
    "/farmlands",
    response_model=list[FarmlandRead],
    summary="List all my farmlands",
)
def list_my_farmlands(farmer_id: CurrentFarmerId, db: DbSession) -> list[FarmlandRead]:
    """Return all farmlands owned by the authenticated farmer."""
    farmlands = list(
        db.scalars(select(Farmland).where(Farmland.farmer_id == farmer_id))
    )
    return [FarmlandRead.model_validate(f) for f in farmlands]


@router.post(
    "/farmlands",
    response_model=FarmlandRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new farmland",
)
def create_farmland(
    payload: FarmlandCreate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
) -> FarmlandRead:
    """Create a new farmland for the authenticated farmer.

    Only name and land area are required. All other profile fields can be
    filled in later via PATCH — the onboarding status endpoint will tell
    the chat exactly which fields are still missing.

    After creating the farmland, immediately call:
      GET /farmlands/{id}/onboarding-status
    to start the guided onboarding conversation.
    """
    farmland = Farmland(
        farmer_id=farmer_id,
        **payload.model_dump(),
    )
    db.add(farmland)
    db.commit()
    db.refresh(farmland)
    return FarmlandRead.model_validate(farmland)


@router.get(
    "/farmlands/{farmland_id}",
    response_model=FarmlandRead,
    summary="Get a farmland's full profile",
)
def get_farmland(
    farmland_id: UUID,
    farmer_id: CurrentFarmerId,
    db: DbSession,
) -> FarmlandRead:
    """Return a specific farmland's complete profile.

    Module 4 (Weather) calls this for the real latitude/longitude to query
    the NASA POWER API instead of using the hardcoded demo coordinates.
    Module 2 (Crop Advisor) reads soil_type, irrigation, water_source, and
    farming_method to determine which crops are suitable.
    """
    farmland = _get_owned_farmland(db, farmland_id, farmer_id)
    return FarmlandRead.model_validate(farmland)


@router.patch(
    "/farmlands/{farmland_id}",
    response_model=FarmlandRead,
    summary="Update a farmland's profile fields",
)
def update_farmland(
    farmland_id: UUID,
    payload: FarmlandUpdate,
    farmer_id: CurrentFarmerId,
    db: DbSession,
) -> FarmlandRead:
    """Partially update a farmland. Only fields you include in the request are changed.

    This is the core write endpoint for the onboarding conversation.
    When the farmer answers "my soil is clay loam", the chat calls:
      PATCH /farmlands/{id}  {"soil_type": "clay loam"}
    Then immediately calls GET /farmlands/{id}/onboarding-status for the next question.
    """
    farmland = _get_owned_farmland(db, farmland_id, farmer_id)

    # exclude_unset=True means only fields explicitly sent in the request are updated.
    # Fields omitted from the request body are left unchanged in the DB.
    update_data = payload.model_dump(exclude_unset=True)
    latitude = update_data.get("latitude", farmland.latitude)
    longitude = update_data.get("longitude", farmland.longitude)
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Latitude and longitude must be provided together.",
        )
    for field, value in update_data.items():
        setattr(farmland, field, value)

    db.commit()
    db.refresh(farmland)
    return FarmlandRead.model_validate(farmland)


# ── Onboarding status route ───────────────────────────────────────────────────

@router.get(
    "/farmlands/{farmland_id}/onboarding-status",
    response_model=OnboardingStatusRead,
    summary="Get what profile fields are filled and what to ask next",
)
def get_onboarding_status(
    farmland_id: UUID,
    farmer_id: CurrentFarmerId,
    db: DbSession,
) -> OnboardingStatusRead:
    """Return the onboarding completion state for a farmland.

    The conversational chat calls this after every farmer answer to know
    what to ask next. When percent_complete reaches 100 and is_complete
    is True, the onboarding conversation is finished and Module 2 can
    begin suggesting crops.

    Response contains:
      - percent_complete  : 0–100 completion percentage
      - next_question     : machine name of the next field to fill
      - next_question_label: the human-readable question to show/speak
      - missing_fields    : list of all fields still not answered
      - fields            : full breakdown of every field's status
    """
    farmland = _get_owned_farmland(db, farmland_id, farmer_id)
    profile = db.scalar(
        select(FarmerProfile).where(FarmerProfile.farmer_id == farmer_id)
    )
    status = _compute_onboarding_status(farmland, profile)

    # Stamp the farmer profile the first time onboarding reaches 100%.
    # This lets downstream modules skip the onboarding nudge for farmers
    # who have already completed it.
    if profile is not None and status.is_complete and profile.onboarding_completed_at is None:
        from datetime import datetime, timezone
        profile.onboarding_completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)

    return status
