"""HTTP API for Module 2 crop advice and season lifecycle."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.core import Farmland
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
from app.services import m2_advisor

router = APIRouter(prefix="/advisor", tags=["Crop Advisor & Season Lifecycle"])
DbSession = Annotated[Session, Depends(get_db)]
FarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


def _require_owned_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> None:
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found")


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


@router.post("/recommendations", response_model=CropRecommendationSet)
def create_recommendations(
    profile: FarmProfileInput,
    db: DbSession,
    farmer_id: FarmerId,
):
    """Recommend from approved knowledge; accepts an M1 contract-shaped mock profile."""
    if profile.farmland_id is not None:
        _require_owned_farmland(db, profile.farmland_id, farmer_id)
    if profile.farmer_id is not None and profile.farmer_id != farmer_id:
        raise HTTPException(status_code=404, detail="Farmland not found")
    try:
        return m2_advisor.recommend_crops(db, profile)
    except (m2_advisor.M2NotFoundError, m2_advisor.M2ConflictError, ValueError) as exc:
        _raise_domain_error(exc)


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
