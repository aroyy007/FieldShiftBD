"""HTTP API for Module 2 crop advice and season lifecycle."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.core import Crop, CropVariety, Farmland
from app.models.season import (
    CropRecommendation as CropRecommendationRecord,
    Season,
)
from app.schemas.m2_advisor import (
    CropRecommendation,
    CropRecommendationSet,
    CropSelectionRequest,
    FarmProfileInput,
    HarvestGuidance,
    SeasonOutcomeInput,
    SeasonOutcomeResponse,
    SeasonPlanCreate,
    SeasonPlanResponse,
    SeasonResponse,
)
from app.schemas.m2_rotation import RotationComparisonRequest, RotationComparisonResponse
from app.services import m2_advisor
from app.services.nasa_power_climate import fetch_rotation_climate
from app.services.rotation_comparison import compare_rotation_patterns

router = APIRouter(prefix="/advisor", tags=["Crop Advisor & Season Lifecycle"])
DbSession = Annotated[Session, Depends(get_db)]
FarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


def _require_owned_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> Farmland:
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found")
    return farmland


def _require_owned_season(db: Session, season_id: UUID, farmer_id: UUID) -> None:
    season = db.scalar(
        select(Season)
        .join(Farmland, Farmland.id == Season.farmland_id)
        .where(Season.id == season_id, Farmland.farmer_id == farmer_id)
    )
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")


def _require_owned_recommendation(
    db: Session, recommendation_id: UUID, farmer_id: UUID
) -> None:
    recommendation = db.scalar(
        select(CropRecommendationRecord)
        .join(Farmland, Farmland.id == CropRecommendationRecord.farmland_id)
        .where(
            CropRecommendationRecord.id == recommendation_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")


def _raise_domain_error(exc: Exception) -> None:
    if isinstance(exc, m2_advisor.M2NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, m2_advisor.M2ConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise exc


def _recommend_for_saved_farmland(
    db: Session, farmland_id: UUID, farmer_id: UUID, crop_preferences: list[UUID] | None = None
) -> CropRecommendationSet:
    farmland = _require_owned_farmland(db, farmland_id, farmer_id)
    profile = m2_advisor.profile_from_farmland(db, farmland, crop_preferences)
    try:
        return m2_advisor.recommend_crops(db, profile, profile_source="m1_saved_farmland")
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        _raise_domain_error(exc)


@router.post("/recommendations", response_model=CropRecommendationSet)
def create_recommendations(
    profile: FarmProfileInput,
    db: DbSession,
    farmer_id: FarmerId,
):
    """Recommend crops for a saved farmland from approved knowledge.

    The saved M1 farmland and farmer profile are authoritative: profile values in
    the request body are not used, so persisted recommendations always match the
    saved profile. Only ``farmland_id``, ``farmer_id``, and ``crop_preferences``
    are read from the body.
    """
    if profile.farmer_id is not None and profile.farmer_id != farmer_id:
        raise HTTPException(status_code=404, detail="Farmland not found")
    if profile.farmland_id is None:
        _raise_domain_error(ValueError("farmland_id is required to scope and persist recommendations"))
    return _recommend_for_saved_farmland(db, profile.farmland_id, farmer_id, profile.crop_preferences)


@router.post("/farmlands/{farmland_id}/recommendations", response_model=CropRecommendationSet)
def create_farmland_recommendations(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    """Recommend crops using only the saved M1 profile for this farmland."""
    return _recommend_for_saved_farmland(db, farmland_id, farmer_id)


@router.get("/farmlands/{farmland_id}/recommendations", response_model=list[CropRecommendation])
def get_recommendations(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_farmland(db, farmland_id, farmer_id)
    try:
        return m2_advisor.list_recommendations(db, farmland_id)
    except m2_advisor.M2NotFoundError as exc:
        _raise_domain_error(exc)


@router.post(
    "/farmlands/{farmland_id}/rotation-comparisons",
    response_model=RotationComparisonResponse,
)
def create_rotation_comparison(
    farmland_id: UUID,
    payload: RotationComparisonRequest,
    db: DbSession,
    farmer_id: FarmerId,
):
    """Compare BRRI-published crop patterns against this farm's saved context.

    This is read-only. It does not create recommendations, seasons, tasks, or
    Module 3 farm-state records.
    """
    farmland = _require_owned_farmland(db, farmland_id, farmer_id)
    latest_season = db.scalar(
        select(Season)
        .where(Season.farmland_id == farmland_id, Season.status == "completed")
        .order_by(Season.actual_harvest_date.desc().nullslast(), Season.created_at.desc())
        .limit(1)
    )
    active_season = db.scalar(
        select(Season)
        .where(Season.farmland_id == farmland_id, Season.status == "active")
        .order_by(Season.created_at.desc())
        .limit(1)
    )
    previous_crop = farmland.previous_crop
    if not previous_crop and latest_season is not None:
        crop = db.get(Crop, latest_season.crop_id)
        previous_crop = crop.name if crop is not None else None
    current_crop = None
    current_variety = None
    if active_season is not None:
        crop = db.get(Crop, active_season.crop_id)
        current_crop = crop.name if crop is not None else None
        if active_season.crop_variety_id is not None:
            variety = db.get(CropVariety, active_season.crop_variety_id)
            current_variety = variety.name if variety is not None else active_season.variety_name
        else:
            current_variety = active_season.variety_name
    return compare_rotation_patterns(
        farmland,
        payload.priorities,
        previous_crop=previous_crop,
        current_crop=current_crop,
        current_variety=current_variety,
        climate_context=fetch_rotation_climate(farmland.latitude, farmland.longitude),
    )


@router.post("/recommendations/{recommendation_id}/dismiss", response_model=CropRecommendation)
def dismiss_recommendation(
    recommendation_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_recommendation(db, recommendation_id, farmer_id)
    try:
        return m2_advisor.dismiss_recommendation(db, recommendation_id)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError) as exc:
        _raise_domain_error(exc)


@router.post("/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
def select_crop(
    data: CropSelectionRequest,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_farmland(db, data.farmland_id, farmer_id)
    if data.farmer_id is not None and data.farmer_id != farmer_id:
        raise HTTPException(status_code=404, detail="Farmland not found")
    try:
        return m2_advisor.select_crop(
            db, farmland_id=data.farmland_id, farmer_id=farmer_id,
            crop_id=data.crop_id, crop_variety_id=data.crop_variety_id,
            variety_name=data.variety_name, recommendation_id=data.recommendation_id,
            planting_date=data.planting_date, expected_harvest_date=data.expected_harvest_date,
            budget_amount=data.budget_amount, budget_currency=data.budget_currency,
        )
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        _raise_domain_error(exc)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A conflicting season already exists") from exc


@router.get("/farmlands/{farmland_id}/seasons", response_model=list[SeasonResponse])
def get_season_history(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_farmland(db, farmland_id, farmer_id)
    try:
        return m2_advisor.list_seasons(db, farmland_id)
    except m2_advisor.M2NotFoundError as exc:
        _raise_domain_error(exc)


@router.post("/seasons/{season_id}/activate", response_model=SeasonResponse)
def activate_season(
    season_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_season(db, season_id, farmer_id)
    try:
        return m2_advisor.activate_season(db, season_id)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        db.rollback()
        _raise_domain_error(exc)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Another season is already active on this farmland") from exc


@router.post("/seasons/{season_id}/plan", response_model=SeasonPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_season_plan(
    season_id: UUID,
    data: SeasonPlanCreate,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_season(db, season_id, farmer_id)
    try:
        return m2_advisor.create_season_plan(db, season_id, data)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        db.rollback()
        _raise_domain_error(exc)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The season plan conflicts with existing data") from exc


@router.get("/seasons/{season_id}/plan", response_model=SeasonPlanResponse)
def get_season_plan(
    season_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_season(db, season_id, farmer_id)
    try:
        return m2_advisor.get_season_plan(db, season_id)
    except m2_advisor.M2NotFoundError as exc:
        _raise_domain_error(exc)


@router.get("/seasons/{season_id}/harvest-guidance", response_model=HarvestGuidance)
def harvest_guidance(
    season_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    _require_owned_season(db, season_id, farmer_id)
    try:
        return m2_advisor.get_harvest_guidance(db, season_id)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError) as exc:
        _raise_domain_error(exc)


@router.post("/seasons/{season_id}/close", response_model=SeasonOutcomeResponse)
def close_season(
    season_id: UUID,
    data: SeasonOutcomeInput,
    db: DbSession,
    farmer_id: FarmerId,
):
    if data.season_id != season_id:
        raise HTTPException(status_code=422, detail="season_id in path and body must match")
    _require_owned_season(db, season_id, farmer_id)
    try:
        return m2_advisor.close_season(db, data)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        db.rollback()
        _raise_domain_error(exc)
