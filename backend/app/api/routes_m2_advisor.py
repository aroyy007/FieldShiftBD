"""HTTP API for Module 2 crop advice and season lifecycle."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.config import settings
from app.core.database import get_db
from app.contracts.challenge.ports import ArtifactNotFound
from app.models.core import AgriculturalKnowledge, Crop, Farmland
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
from app.schemas.planting_window import PlantingWindowEvidence, unavailable_provenance
from app.services import m2_advisor
from app.services.climate.power_history import NasaPowerHistoryProvider
from app.services.planting_window_analysis import compare_annual_onsets
from app.services.rain_onset import accumulate_growing_degree_days

router = APIRouter(prefix="/advisor", tags=["Crop Advisor & Season Lifecycle"])
DbSession = Annotated[Session, Depends(get_db)]
FarmerId = Annotated[UUID, Depends(get_current_farmer_id)]

NASA_HISTORY_START = date(2001, 1, 1)
NASA_HISTORY_END = date(2025, 12, 31)


def _planting_evidence_response(
    status_value: str,
    message_bn: str,
    message_en: str,
    farmland: Farmland,
    season: Season,
    crop: Crop,
    *,
    calendar=None,
    comparison=None,
    recommended_shift_days=None,
    gdd=None,
    provenance=None,
) -> PlantingWindowEvidence:
    return PlantingWindowEvidence(
        status=status_value,
        message_bn=message_bn,
        message_en=message_en,
        farmland_id=str(farmland.id),
        season_id=str(season.id),
        crop_name=crop.name,
        annual_comparison=comparison,
        recommended_shift_days=recommended_shift_days,
        gdd_summary=gdd,
        planting_calendar=calendar,
        data_provenance=provenance or unavailable_provenance(),
        limitations_bn=["NASA POWER প্রায় ৫০ কিমি এলাকার আবহাওয়া দেখায়; এটি আপনার জমির সরাসরি পরিমাপ নয়।"],
        limitations_en=["NASA POWER describes weather over an approximately 50 km area; it is not a direct measurement of this field."],
    )


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
    district_code = (farmland.district or "BD").strip().lower().replace(" ", "-")[:24]
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


@router.get(
    "/farmlands/{farmland_id}/planting-window",
    response_model=PlantingWindowEvidence,
)
def planting_window_evidence(
    farmland_id: UUID,
    season_id: UUID,
    db: DbSession,
    farmer_id: FarmerId,
):
    """Return historical NASA onset evidence only for the farmer's own season.

    A planting calendar is considered verified only when an approved and
    reviewed crop-calendar record contains the documented structured fields.
    Missing agronomic evidence returns a useful insufficiency response and
    never turns a climate observation into a planting recommendation.
    """
    farmland = _require_owned_farmland(db, farmland_id, farmer_id)
    season = db.scalar(
        select(Season).where(Season.id == season_id, Season.farmland_id == farmland_id)
    )
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")
    crop = db.get(Crop, season.crop_id)
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found")

    knowledge_rows = db.scalars(
        select(AgriculturalKnowledge).where(
            AgriculturalKnowledge.crop_id == crop.id,
            AgriculturalKnowledge.category == "crop_calendar",
            AgriculturalKnowledge.review_status == "approved",
            AgriculturalKnowledge.reviewed_by.is_not(None),
            AgriculturalKnowledge.reviewed_at.is_not(None),
            (AgriculturalKnowledge.effective_from.is_(None)
             | (AgriculturalKnowledge.effective_from <= date.today())),
            (AgriculturalKnowledge.effective_to.is_(None)
             | (AgriculturalKnowledge.effective_to >= date.today())),
        ).order_by(AgriculturalKnowledge.crop_variety_id.is_(None))
    ).all()
    calendar_row = next((row for row in knowledge_rows if
                         row.crop_variety_id in (None, season.crop_variety_id)
                         and row.region_code in (None, district_code)
                         and isinstance(row.content, dict)
                         and isinstance(row.content.get("planting_window"), dict)
                         and isinstance(row.content.get("gdd"), dict)), None)
    if calendar_row is None:
        return _planting_evidence_response(
            "insufficient_data",
            "এই ফসলের জন্য যাচাইকৃত রোপণ ক্যালেন্ডার ও GDD তাপমাত্রা-ভিত্তি নেই। তাই এখন নির্ভরযোগ্য পরামর্শ দেওয়া যাচ্ছে না।",
            "There is no reviewed crop calendar and GDD temperature base for this crop yet, so a reliable planting advisory cannot be given.",
            farmland, season, crop,
        )

    planting = calendar_row.content["planting_window"]
    gdd_config = calendar_row.content["gdd"]
    shift_policy = planting.get("onset_shift_policy")
    try:
        start_month = int(planting["season_start_month"])
        start_day = int(planting["season_start_day"])
        end_month = int(planting["season_end_month"])
        end_day = int(planting["season_end_day"])
        base_temperature = float(gdd_config["base_temperature_c"])
        cap_temperature = (float(gdd_config["cap_temperature_c"])
                           if gdd_config.get("cap_temperature_c") is not None else None)
        # Validate ranges before data acquisition, including month/day combinations.
        date(2024, start_month, start_day)
        date(2024, end_month, end_day)
        if not (-10 <= base_temperature <= 40) or (
            cap_temperature is not None and not base_temperature <= cap_temperature <= 55
        ):
            raise ValueError("invalid GDD temperature range")
        if shift_policy != "shift_window_by_observed_onset_delta":
            raise ValueError("crop calendar has no reviewed onset-to-window shift policy")
    except (KeyError, TypeError, ValueError):
        return _planting_evidence_response(
            "insufficient_data",
            "যাচাইকৃত ফসল ক্যালেন্ডারে মৌসুমের তারিখ, GDD ভিত্তি বা রোপণ-সময় সামঞ্জস্যের নীতি অসম্পূর্ণ।",
            "The reviewed crop calendar is missing valid season dates, a GDD base, or an approved planting-window adjustment policy.",
            farmland, season, crop,
        )

    if farmland.latitude is None or farmland.longitude is None:
        return _planting_evidence_response(
            "insufficient_data",
            "এই জমির সংরক্ষিত অবস্থান নেই। NASA আবহাওয়া তথ্যের জন্য জমির অবস্থান যোগ করুন।",
            "This farm has no saved coordinates. Add its location to retrieve NASA climate data.",
            farmland, season, crop,
            calendar={"source_name": calendar_row.source_name,
                      "source_reference": calendar_row.source_reference,
                      "reviewed_at": calendar_row.reviewed_at.isoformat()},
        )

    provider = NasaPowerHistoryProvider(settings.CLIMATE_CACHE_DIR)
    latitude, longitude = float(farmland.latitude), float(farmland.longitude)
    cache_status = "hit" if provider.has_cached_bundle(
        district_code, latitude, longitude, NASA_HISTORY_START, NASA_HISTORY_END
    ) else "miss"
    try:
        bundle = provider.get_bundle(
            district_code, latitude, longitude, NASA_HISTORY_START, NASA_HISTORY_END,
            offline=settings.OFFLINE_MODE,
        )
    except ArtifactNotFound:
        return _planting_evidence_response(
            "unavailable",
            "এই এলাকার ২০০১–২০২৫ সালের NASA ডেটা ক্যাশে নেই; ইন্টারনেট সংযোগে আবার চেষ্টা করুন।",
            "NASA data for 2001–2025 is not cached for this location. Retry while online.",
            farmland, season, crop,
            calendar={"source_name": calendar_row.source_name,
                      "source_reference": calendar_row.source_reference},
            provenance={**unavailable_provenance(cache_status="miss"), "district_code": district_code},
        )
    except (RuntimeError, ValueError):
        return _planting_evidence_response(
            "unavailable",
            "NASA ডেটা এখন পাওয়া যাচ্ছে না। পরে আবার চেষ্টা করুন।",
            "NASA climate data is temporarily unavailable. Please try again later.",
            farmland, season, crop,
            calendar={"source_name": calendar_row.source_name,
                      "source_reference": calendar_row.source_reference},
            provenance={**unavailable_provenance(cache_status="miss"),
                        "district_code": district_code},
        )

    if cache_status == "miss":
        cache_status = "fetched_live_and_cached"

    rainfall = {item.date: item.rainfall_mm for item in bundle.daily_series}
    temperature = {item.date: item.temperature_c for item in bundle.daily_series}
    comparison = compare_annual_onsets(
        rainfall,
        season_start_month=start_month,
        season_start_day=start_day,
        season_end_month=end_month,
        season_end_day=end_day,
    )
    annual_gdd = []
    for year in range(2001, 2026):
        try:
            start = date(year, start_month, start_day)
            end_year = year + (1 if (end_month, end_day) < (start_month, start_day) else 0)
            end = date(end_year, end_month, end_day)
        except ValueError:
            continue
        gdd = accumulate_growing_degree_days(
            temperature, start, end, base_temperature_c=base_temperature,
            cap_temperature_c=cap_temperature,
        )
        annual_gdd.append({"year": year, "total_degree_days": gdd.total_degree_days,
                           "valid_days": gdd.valid_days, "expected_days": gdd.expected_days})
    valid_gdd = [row["total_degree_days"] for row in annual_gdd if row["total_degree_days"] is not None]
    baseline_gdd = [row["total_degree_days"] for row in annual_gdd
                    if row["year"] <= 2012 and row["total_degree_days"] is not None]
    recent_gdd = [row["total_degree_days"] for row in annual_gdd
                  if row["year"] >= 2013 and row["total_degree_days"] is not None]
    manifest = bundle.manifest
    provenance = {
        "source": "NASA POWER Daily Point",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "dataset": "POWER Daily API, community AG",
        "variables": ["precipitation (mm/day)", "temperature (°C)", "solar radiation (MJ/m²/day)"],
        "temporal_start": manifest.coverage_start,
        "temporal_end": manifest.coverage_end,
        "spatial_resolution_m": 50000,
        "spatial_scale": "area-level grid, approximately 50 km; not field-level",
        "cache_status": cache_status,
        "retrieved_at": manifest.created_at,
        "district_code": district_code,
        "coverage_by_variable": [item.model_dump() for item in manifest.coverage_by_variable],
    }
    enough = (comparison["status"] == "available" and len(baseline_gdd) >= 9
              and len(recent_gdd) >= 9)
    return _planting_evidence_response(
        "available" if enough else "insufficient_data",
        ("ঐতিহাসিক বৃষ্টির সময় ও GDD তুলনা পাওয়া গেছে। এটি পর্যবেক্ষিত তথ্য; একে সরাসরি রোপণের তারিখের সুপারিশ হিসেবে ধরবেন না।"
         if enough else "NASA ডেটার পর্যাপ্ত সম্পূর্ণ বছর নেই; নির্ভরযোগ্য তুলনা বা পরামর্শ দেওয়া যাচ্ছে না।"),
        ("Historical rainfall-onset and GDD comparisons are available. These are observations, not a direct planting-date recommendation."
         if enough else "There are not enough complete NASA data years for a reliable comparison or advisory."),
        farmland, season, crop,
        calendar={"source_name": calendar_row.source_name,
                  "source_reference": calendar_row.source_reference,
                  "reviewed_at": calendar_row.reviewed_at.isoformat(),
                  "season_start_month": start_month, "season_start_day": start_day,
                  "season_end_month": end_month, "season_end_day": end_day,
                  "gdd_base_temperature_c": base_temperature,
                  "gdd_cap_temperature_c": cap_temperature},
        comparison=comparison,
        recommended_shift_days=(comparison["observed_shift_days"] if enough else None),
        gdd={"method": "daily_mean_max_zero_v1", "annual_values": annual_gdd,
             "valid_year_count": len(valid_gdd),
             "baseline_valid_years": len(baseline_gdd),
             "recent_valid_years": len(recent_gdd),
             "baseline_mean": round(sum(baseline_gdd) / len(baseline_gdd), 2) if baseline_gdd else None,
             "recent_mean": round(sum(recent_gdd) / len(recent_gdd), 2) if recent_gdd else None},
        provenance=provenance,
    )


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
