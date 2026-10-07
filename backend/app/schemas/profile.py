from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re

# Allow common visual separators when farmers type their number, but always
# normalize to digits-only after the leading +. Keeps the storage format
# predictable for lookup while being forgiving about input.
_PHONE_STRIP_RE = re.compile(r"[\s\-()]")


def _normalize_phone(v: str) -> str:
    """Trim whitespace and remove spaces/dashes/parens, but preserve the leading +."""
    cleaned = _PHONE_STRIP_RE.sub("", v.strip())
    return cleaned

# ── Auth schemas ──────────────────────────────────────────────────────────────
class FarmerRegisterRequest(BaseModel):
    """What the app sends when a new farmer signs up."""
    name: str = Field(min_length=1, max_length=200)
    # Allow up to 20 chars so international formats with extensions fit.
    phone_e164: str = Field(min_length=8, max_length=20)

    @field_validator("phone_e164")
    @classmethod
    def phone_must_be_e164(cls, v: str) -> str:
        normalized = _normalize_phone(v)
        if (
            not normalized.startswith("+")
            or not normalized[1:].isdigit()
            or not (7 <= len(normalized) - 1 <= 15)
        ):
            raise ValueError(
                "Phone must be in international format, e.g. +8801712345678"
            )
        return normalized


class FarmerLoginRequest(BaseModel):
    """What the app sends when an existing farmer logs in."""
    phone_e164: str = Field(min_length=8, max_length=20)

    @field_validator("phone_e164")
    @classmethod
    def phone_must_be_e164(cls, v: str) -> str:
        normalized = _normalize_phone(v)
        if (
            not normalized.startswith("+")
            or not normalized[1:].isdigit()
            or not (7 <= len(normalized) - 1 <= 15)
        ):
            raise ValueError(
                "Phone must be in international format, e.g. +8801712345678"
            )
        return normalized
class TokenResponse(BaseModel):
    """What the backend returns after a successful register or login."""
    access_token: str
    token_type: str = "bearer"
    farmer_id: UUID
# ── Farmer schemas ────────────────────────────────────────────────────────────
class FarmerRead(BaseModel):
    """Farmer identity — safe to return to the client."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    phone_e164: str
    created_at: datetime
# ── Farmland schemas ──────────────────────────────────────────────────────────
AreaUnit = Literal["square_metre", "decimal", "acre", "hectare"]
FarmingMethod = Literal["organic", "conventional", "mixed"]
# PostgreSQL NUMERIC(14, 3) can store values up to 99,999,999,999.999.
MAX_LAND_AREA_SQM = Decimal("99999999999.999")
MAX_BUDGET_AMOUNT = Decimal("999999999999.99")
MAX_YIELD_AMOUNT = Decimal("99999999999.999")
MAX_FARMING_EXPERIENCE_YEARS = Decimal("999.9")


class FarmlandCreate(BaseModel):
    """Fields required and optional when creating a new farmland.
    Only name + land area are required up-front. Everything else can be
    filled in later via PATCH — the onboarding status endpoint tells you
    what's still missing.
    """
    name: str = Field(min_length=1, max_length=200)
    land_area_sqm: Decimal = Field(gt=0, le=MAX_LAND_AREA_SQM)
    land_area_display_unit: AreaUnit = "decimal"
    # Location — filled in during onboarding conversation
    division: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    upazila: str | None = Field(default=None, max_length=120)
    village_or_locality: str | None = Field(default=None, max_length=200)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    # Farm characteristics — filled in during onboarding
    soil_type: str | None = Field(default=None, max_length=120)
    irrigation_available: bool | None = None
    water_source: str | None = Field(default=None, max_length=120)
    farming_method: FarmingMethod | None = None
    # Economics — filled in during onboarding
    budget_amount: Decimal | None = Field(default=None, ge=0, le=MAX_BUDGET_AMOUNT)
    budget_currency: str = "BDT"
    # Previous season history — filled in during onboarding
    previous_crop: str | None = Field(default=None, max_length=160)
    previous_yield_amount: Decimal | None = Field(default=None, ge=0, le=MAX_YIELD_AMOUNT)
    previous_yield_unit: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def coordinates_must_be_paired(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class FarmlandUpdate(BaseModel):
    """Every field is optional — PATCH updates only what you send.
    This is what the onboarding chat calls after each farmer answer.
    Example: farmer says "my soil is clay" → PATCH {"soil_type": "clay"}
    """
    name: str | None = Field(default=None, min_length=1, max_length=200)
    division: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    upazila: str | None = Field(default=None, max_length=120)
    village_or_locality: str | None = Field(default=None, max_length=200)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    land_area_sqm: Decimal | None = Field(default=None, gt=0, le=MAX_LAND_AREA_SQM)
    land_area_display_unit: AreaUnit | None = None
    soil_type: str | None = Field(default=None, max_length=120)
    irrigation_available: bool | None = None
    water_source: str | None = Field(default=None, max_length=120)
    farming_method: FarmingMethod | None = None
    budget_amount: Decimal | None = Field(default=None, ge=0, le=MAX_BUDGET_AMOUNT)
    budget_currency: str | None = None
    previous_crop: str | None = Field(default=None, max_length=160)
    previous_yield_amount: Decimal | None = Field(default=None, ge=0, le=MAX_YIELD_AMOUNT)
    previous_yield_unit: str | None = Field(default=None, max_length=32)
class FarmlandRead(BaseModel):
    """Full farmland response — everything the client needs to display the profile."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    farmer_id: UUID
    name: str
    country_code: str
    division: str | None
    district: str | None
    upazila: str | None
    village_or_locality: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    land_area_sqm: Decimal
    land_area_display_unit: str
    soil_type: str | None
    irrigation_available: bool | None
    water_source: str | None
    farming_method: str | None
    budget_amount: Decimal | None
    budget_currency: str
    previous_crop: str | None
    previous_yield_amount: Decimal | None
    previous_yield_unit: str | None
    created_at: datetime
    updated_at: datetime
# ── Farmer profile schemas ────────────────────────────────────────────────────
class FarmerProfileUpdate(BaseModel):
    """Update farming experience, equipment, livestock, and language preference."""
    farming_experience_years: Decimal | None = Field(
        default=None, ge=0, le=MAX_FARMING_EXPERIENCE_YEARS
    )
    equipment: list[str] | None = None
    livestock: list[str] | None = None
    preferred_language: Literal["bn", "en"] | None = None
class FarmerProfileRead(BaseModel):
    """Farmer profile response — the extended farming details beyond identity."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    farmer_id: UUID
    farming_experience_years: Decimal | None
    equipment: list
    livestock: list
    preferred_language: str
    onboarding_completed_at: datetime | None
# ── Combined profile response ─────────────────────────────────────────────────
class MyProfileRead(BaseModel):
    """Full farmer view: identity + farming profile + all farmlands.
    What GET /profile returns. Module 5 (Chat) uses this as the LLM context
    to answer questions in a farm-specific, personalized way.
    """
    farmer: FarmerRead
    profile: FarmerProfileRead | None
    farmlands: list[FarmlandRead]
# ── Onboarding status schemas ─────────────────────────────────────────────────
class OnboardingFieldStatus(BaseModel):
    """Status of a single profile field in the onboarding checklist."""
    field: str          # Machine-readable field name, e.g. "soil_type"
    label: str          # Human-readable question, e.g. "What type of soil?"
    filled: bool        # True if the farmer has already answered this
class OnboardingStatusRead(BaseModel):
    """The onboarding status response — tells the frontend what to ask next.
    The chat/UI calls GET /farmlands/{id}/onboarding-status after each answer.
    It reads next_question and next_question_label to know what to ask next.
    When is_complete is True, Module 2 can start suggesting crops.
    """
    farmland_id: UUID
    percent_complete: int           # 0–100
    is_complete: bool
    missing_fields: list[str]       # All fields still not filled
    next_question: str | None       # The single next field to ask about
    next_question_label: str | None # The human-readable question for that field
    fields: list[OnboardingFieldStatus]  # Full breakdown of every field
