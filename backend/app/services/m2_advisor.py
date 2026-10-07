"""Business logic for crop recommendations and the season lifecycle (M2)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Crop, CropVariety, Farmland
from app.models.season import (
    CropRecommendation as CropRecommendationRecord,
    GrowthStage,
    Season,
    SeasonPlan,
)
from app.schemas.m2_advisor import (
    CropRecommendation,
    CropRecommendationSet,
    CropIdentity,
    FarmProfileInput,
    GrowthStageDefinition,
    HarvestGuidance,
    InitialTaskDefinition,
    KnowledgeReference,
    RecommendationReasoning,
    RecommendationSetStatus,
    SeasonOutcomeInput,
    SeasonOutcomeResponse,
    SeasonPlanCreate,
    SeasonPlanResponse,
    SeasonResponse,
    SuitabilityFactor,
)
from app.services.m2_knowledge import AgriculturalEvidence, KnowledgeQuery, get_relevant_evidence


class M2NotFoundError(Exception):
    """An M2-owned resource or its parent does not exist."""


class M2ConflictError(Exception):
    """A requested lifecycle transition conflicts with existing state."""


FARM_TIMEZONE = ZoneInfo("Asia/Dhaka")


def _farm_today() -> date:
    """Use Bangladesh's calendar date for effective agricultural evidence."""
    return datetime.now(FARM_TIMEZONE).date()


def _knowledge_ref(row: AgriculturalEvidence) -> KnowledgeReference:
    return KnowledgeReference(
        knowledge_id=row.id,
        source_name=row.source_name,
        source_type=row.source_type,
        source_reference=row.source_reference,
        category=row.category,
        region_code=row.region_code,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        review_status=row.review_status,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        acceptance_method=getattr(row, "acceptance_method", None),
    )


def _approved_knowledge(
    db: Session,
    crop_id: UUID,
    today: date,
    crop_variety_id: UUID | None = None,
    region_values: set[str] | None = None,
    context: dict[str, Any] | None = None,
    categories: set[str] | None = None,
    crop_name: str | None = None,
) -> list[AgriculturalEvidence]:
    query = KnowledgeQuery(
        crop_id=crop_id,
        crop_name=crop_name,
        crop_variety_id=crop_variety_id,
        categories=frozenset(categories or ()),
        region_codes=frozenset(region_values or ()),
        context=context or {},
        as_of=today,
    )
    return list(get_relevant_evidence(db, query).items)


def _profile_context(profile: FarmProfileInput, planting_date: date | None = None) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in (
        "soil_type", "irrigation_available", "water_source", "farming_method",
        "land_area", "land_unit", "land_area_sqm", "budget_amount",
        "farming_experience_years",
    ):
        value = getattr(profile, key, None)
        if value is not None:
            context[key] = value
    if profile.location:
        for key in ("country_code", "division", "district", "upazila"):
            value = getattr(profile.location, key, None)
            if value is not None:
                context[key] = value
    if planting_date:
        context["planting_date"] = planting_date.isoformat()
        context["planting_month"] = planting_date.month
        context["planting_year"] = planting_date.year
    return context


def _profile_regions(profile: FarmProfileInput) -> set[str]:
    values = set()
    if profile.location:
        values.update((profile.location.country_code, profile.location.division,
                       profile.location.district, profile.location.upazila))
    return {value for value in values if value}


def _season_profile(farmland: Farmland, season: Season) -> FarmProfileInput:
    return FarmProfileInput(
        farmland_id=farmland.id,
        farmer_id=farmland.farmer_id,
        location={
            "country_code": farmland.country_code,
            "division": farmland.division,
            "district": farmland.district,
            "upazila": farmland.upazila,
            "village_or_locality": farmland.village_or_locality,
            "latitude": farmland.latitude,
            "longitude": farmland.longitude,
        },
        land_area_sqm=farmland.land_area_sqm,
        soil_type=farmland.soil_type,
        irrigation_available=farmland.irrigation_available,
        water_source=farmland.water_source,
        farming_method=farmland.farming_method,
        budget_amount=getattr(season, "budget_amount", None),
    )


def _select_season_plan_knowledge(
    rows: list[AgriculturalEvidence], crop_variety_id: UUID | None
) -> AgriculturalEvidence | None:
    plan_rows = [
        row for row in rows if row.category in {"season_plan", "crop_calendar"}
    ]
    if crop_variety_id is not None:
        variety_specific = next(
            (row for row in plan_rows if row.crop_variety_id == crop_variety_id),
            None,
        )
        if variety_specific is not None:
            return variety_specific
    return next((row for row in plan_rows if row.crop_variety_id is None), None)


def _as_factor(value: Any, fallback: str, references: list[KnowledgeReference]) -> SuitabilityFactor | None:
    if value is None:
        return None
    if isinstance(value, dict):
        label = str(value.get("factor") or fallback)
        explanation = value.get("explanation") or value.get("summary") or value.get("text")
        refs = references
    else:
        label, explanation, refs = fallback, value, references
    if not isinstance(explanation, str) or not explanation.strip():
        return None
    return SuitabilityFactor(factor=label, explanation=explanation.strip(), knowledge_refs=refs)


def _matches_profile(condition: Any, profile: FarmProfileInput) -> bool:
    """Match only explicitly supported, present profile fields; fail closed otherwise."""
    if not isinstance(condition, dict) or not condition:
        return False
    scalar_fields = {
        "soil_type": profile.soil_type,
        "irrigation_available": profile.irrigation_available,
        "water_source": profile.water_source,
        "farming_method": profile.farming_method,
    }
    location_fields = {
        "country_code": profile.location.country_code if profile.location else None,
        "division": profile.location.division if profile.location else None,
        "district": profile.location.district if profile.location else None,
        "upazila": profile.location.upazila if profile.location else None,
    }
    for key, expected in condition.items():
        actual = scalar_fields.get(key, location_fields.get(key))
        if actual is None:
            return False
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(str(actual).strip().casefold() == str(value).strip().casefold() for value in allowed):
            return False
    return True


def _recommendation_reasoning(
    profile: FarmProfileInput, rows: list[AgriculturalEvidence]
) -> tuple[RecommendationReasoning, list[KnowledgeReference]]:
    recommendation_rows = [
        row for row in rows
        if not (
            isinstance(row.content, dict)
            and row.content.get("evidence_role") == "regional_context_only"
        )
    ]
    refs = [_knowledge_ref(row) for row in recommendation_rows]
    values: dict[str, list[SuitabilityFactor]] = {
        "positive_factors": [],
        "limiting_factors": [],
        "risks_or_concerns": [],
    }
    for reference_index, row in enumerate(recommendation_rows):
        payload = row.content if isinstance(row.content, dict) else {}
        declared = payload.get("factors", {})
        if not isinstance(declared, dict):
            declared = {}
        for group, aliases in (
            ("positive_factors", ("suitable_because", "positive_factors")),
            ("limiting_factors", ("limiting_factors",)),
            ("risks_or_concerns", ("concerns", "risks_or_concerns")),
        ):
            entries: list[Any] = []
            for alias in aliases:
                candidate = payload.get(alias, declared.get(alias))
                if isinstance(candidate, list):
                    entries.extend(candidate)
                elif candidate is not None:
                    entries.append(candidate)
            if isinstance(declared, dict):
                for factor_name, entry in declared.items():
                    if isinstance(entry, dict) and entry.get("kind") == group:
                        entries.append({"factor": factor_name, **entry})
            for entry in entries:
                # Positive fit claims require an explicit matching condition.
                # Unconditional approved knowledge can still describe risks/limits.
                if group == "positive_factors":
                    row_condition = payload.get("applicability")
                    entry_condition = entry.get("when") if isinstance(entry, dict) else None
                    if not (
                        (row_condition is not None and _matches_profile(row_condition, profile))
                        or (entry_condition is not None and _matches_profile(entry_condition, profile))
                    ):
                        continue
                factor = _as_factor(entry, row.category, [refs[reference_index]])
                if factor and factor not in values[group]:
                    values[group].append(factor)

    summary = "Reasoning uses approved agricultural knowledge and factors that match the supplied farm profile."
    return RecommendationReasoning(
        summary=summary,
        positive_factors=values["positive_factors"],
        limiting_factors=values["limiting_factors"],
        risks_or_concerns=values["risks_or_concerns"],
    ), refs


def recommend_crops(db: Session, profile: FarmProfileInput) -> CropRecommendationSet:
    if profile.farmland_id is None:
        raise ValueError("farmland_id is required to scope and persist recommendations")
    farmland = db.get(Farmland, profile.farmland_id)
    if farmland is None:
        raise M2NotFoundError("Farmland not found")
    if profile.farmer_id is not None and farmland.farmer_id != profile.farmer_id:
        raise M2NotFoundError("Farmland not found")

    preference_ids = set(profile.crop_preferences)
    if not preference_ids:
        from app.models.core import FarmlandCropPreference
        preference_ids = set(db.scalars(select(FarmlandCropPreference.crop_id).where(
            FarmlandCropPreference.farmland_id == farmland.id
        )))

    crops = list(db.scalars(select(Crop).order_by(Crop.name)))
    crops.sort(key=lambda crop: (crop.id not in preference_ids, crop.name.casefold()))
    results: list[CropRecommendation] = []
    today = _farm_today()
    has_approved_knowledge = False
    for crop in crops:
        rows = _approved_knowledge(
            db,
            crop.id,
            today,
            region_values=_profile_regions(profile),
            context=_profile_context(profile),
            crop_name=crop.name,
        )
        if not rows:
            continue
        has_approved_knowledge = True
        reasoning, refs = _recommendation_reasoning(profile, rows)
        if not reasoning.positive_factors:
            # Approved references and general crop facts alone do not prove fit.
            continue
        recommendation = CropRecommendationRecord(
            farmland_id=farmland.id,
            crop_id=crop.id,
            score=None,
            status="proposed",
            reasoning=reasoning.model_dump(mode="json"),
            knowledge_refs=[ref.model_dump(mode="json") for ref in refs],
        )
        db.add(recommendation)
        db.flush()
        results.append(CropRecommendation(
            recommendation_id=recommendation.id,
            farmland_id=farmland.id,
            crop=CropIdentity(crop_id=crop.id, name=crop.name, scientific_name=crop.scientific_name),
            score=None,
            status="proposed",
            reasoning=reasoning,
            knowledge_refs=refs,
        ))
    db.commit()
    if results:
        state = RecommendationSetStatus.AVAILABLE
        message = "Recommendations are based on matching factors in approved agricultural knowledge."
    elif has_approved_knowledge:
        state = RecommendationSetStatus.NO_SUPPORTED_FIT
        message = "Approved knowledge is available, but no crop has a supported positive fit for the supplied profile."
    else:
        state = RecommendationSetStatus.NO_APPROVED_KNOWLEDGE
        message = "No approved, currently effective agricultural knowledge applies to this farm; suitability cannot be established."
    return CropRecommendationSet(
        farmland_id=farmland.id, status=state, message=message, recommendations=results
    )


def list_recommendations(db: Session, farmland_id: UUID) -> list[CropRecommendation]:
    rows = db.execute(
        select(CropRecommendationRecord, Crop)
        .join(Crop, Crop.id == CropRecommendationRecord.crop_id)
        .where(CropRecommendationRecord.farmland_id == farmland_id)
        .order_by(CropRecommendationRecord.created_at.desc())
    ).all()
    if db.get(Farmland, farmland_id) is None:
        raise M2NotFoundError("Farmland not found")
    return [CropRecommendation(
        recommendation_id=record.id,
        farmland_id=record.farmland_id,
        crop=CropIdentity(crop_id=crop.id, name=crop.name, scientific_name=crop.scientific_name),
        score=record.score,
        status=record.status,
        reasoning=RecommendationReasoning.model_validate(record.reasoning),
        knowledge_refs=[KnowledgeReference.model_validate(ref) for ref in record.knowledge_refs],
    ) for record, crop in rows]


def dismiss_recommendation(db: Session, recommendation_id: UUID) -> CropRecommendation:
    record = db.get(CropRecommendationRecord, recommendation_id)
    if record is None:
        raise M2NotFoundError("Recommendation not found")
    if record.status != "proposed":
        raise M2ConflictError("Only proposed recommendations can be dismissed")
    record.status = "dismissed"
    db.commit()
    db.refresh(record)
    crop = db.get(Crop, record.crop_id)
    return CropRecommendation(
        recommendation_id=record.id, farmland_id=record.farmland_id,
        crop=CropIdentity(crop_id=crop.id, name=crop.name, scientific_name=crop.scientific_name),
        score=record.score, status=record.status,
        reasoning=RecommendationReasoning.model_validate(record.reasoning),
        knowledge_refs=[KnowledgeReference.model_validate(ref) for ref in record.knowledge_refs],
    )


def select_crop(db: Session, farmland_id: UUID, farmer_id: UUID | None, crop_id: UUID,
                crop_variety_id: UUID | None, variety_name: str | None,
                recommendation_id: UUID | None, planting_date: date | None,
                expected_harvest_date: date | None, budget_amount: Decimal | None,
                budget_currency: str) -> SeasonResponse:
    farmland = db.get(Farmland, farmland_id)
    if farmland is None or (farmer_id is not None and farmland.farmer_id != farmer_id):
        raise M2NotFoundError("Farmland not found")
    if db.get(Crop, crop_id) is None:
        raise M2NotFoundError("Crop not found")
    if crop_variety_id is not None:
        variety = db.get(CropVariety, crop_variety_id)
        if variety is None or variety.crop_id != crop_id:
            raise ValueError("Crop variety must belong to the selected crop")
    if recommendation_id is not None:
        recommendation = db.get(CropRecommendationRecord, recommendation_id)
        if recommendation is None or recommendation.farmland_id != farmland_id or recommendation.crop_id != crop_id:
            raise M2NotFoundError("Matching recommendation not found")
        if recommendation.status != "proposed":
            raise M2ConflictError("Recommendation is no longer proposed")
        recommendation.status = "selected"

    # Guard against piling up planned or active seasons on the same farmland.
    # A farmer should explicitly complete or cancel their current planned/active
    # season before starting a new one. Without this check, repeated select_crop
    # calls accumulate ghost seasons that pollute Module 3 stage/task generation
    # and Module 5 chat context.
    existing_open = db.scalar(
        select(Season).where(
            Season.farmland_id == farmland_id,
            Season.status.in_(["planned", "active"]),
        )
    )
    if existing_open is not None:
        raise M2ConflictError(
            "This farmland already has an open season. "
            "Complete or cancel it before starting a new one."
        )

    season = Season(
        farmland_id=farmland_id, crop_id=crop_id, crop_variety_id=crop_variety_id,
        variety_name=variety_name, planting_date=planting_date,
        expected_harvest_date=expected_harvest_date, status="planned",
        budget_amount=budget_amount, budget_currency=budget_currency,
    )
    db.add(season)
    db.commit()
    db.refresh(season)
    return _season_response(season)
def _season_response(season: Season) -> SeasonResponse:
    return SeasonResponse(
        season_id=season.id, farmland_id=season.farmland_id, crop_id=season.crop_id,
        crop_variety_id=season.crop_variety_id, variety_name=season.variety_name,
        planting_date=season.planting_date, expected_harvest_date=season.expected_harvest_date,
        status=season.status, budget_amount=season.budget_amount,
        budget_currency=season.budget_currency, actual_harvest_date=season.actual_harvest_date,
        actual_yield=season.actual_yield, yield_unit=season.yield_unit,
        outcome_notes=season.outcome_notes, created_at=season.created_at, updated_at=season.updated_at,
    )


def list_seasons(db: Session, farmland_id: UUID) -> list[SeasonResponse]:
    if db.get(Farmland, farmland_id) is None:
        raise M2NotFoundError("Farmland not found")
    return [_season_response(season) for season in db.scalars(
        select(Season).where(Season.farmland_id == farmland_id).order_by(Season.created_at.desc())
    )]


def create_season_plan(db: Session, season_id: UUID, data: SeasonPlanCreate) -> SeasonPlanResponse:
    season = db.get(Season, season_id)
    if season is None or data.season_id != season_id:
        raise M2NotFoundError("Season not found")
    if season.status in {"completed", "cancelled"}:
        raise M2ConflictError("Completed or cancelled seasons cannot receive a new plan")
    if data.status.value not in {"draft", "active"}:
        raise ValueError("A generated plan must be draft or active")
    if season.status == "active":
        raise M2ConflictError(
            "Cannot create or replace an active season plan without coordinating current-stage state with Module 3"
        )
    farmland = db.get(Farmland, season.farmland_id)
    if farmland is None:
        raise M2NotFoundError("Farmland not found")
    profile = _season_profile(farmland, season)
    knowledge = _approved_knowledge(
        db, season.crop_id, _farm_today(), season.crop_variety_id,
        _profile_regions(profile), _profile_context(profile, season.planting_date),
        {"season_plan", "crop_calendar"},
    )
    plan_row = _select_season_plan_knowledge(knowledge, season.crop_variety_id)
    if plan_row is None:
        raise M2ConflictError("No approved season-plan knowledge exists for this crop")
    content = plan_row.content if isinstance(plan_row.content, dict) else {}
    raw_stages = content.get("growth_stages", [])
    raw_tasks = content.get("initial_tasks", [])
    if not isinstance(raw_stages, list) or not raw_stages:
        raise M2ConflictError("Approved season-plan knowledge has no growth_stages")
    stage_defs = [GrowthStageDefinition.model_validate(item) for item in raw_stages]
    stage_defs.sort(key=lambda stage: stage.sequence)
    if len({stage.sequence for stage in stage_defs}) != len(stage_defs):
        raise M2ConflictError("Season-plan knowledge contains duplicate stage sequences")
    plan = SeasonPlan(season_id=season.id, title=data.title, description=data.description,
                      status=data.status.value)
    if data.status.value == "active":
        for prior in db.scalars(select(SeasonPlan).where(
            SeasonPlan.season_id == season.id, SeasonPlan.status == "active"
        )):
            prior.status = "superseded"
    db.add(plan)
    db.flush()
    stages: list[GrowthStage] = []
    for definition in stage_defs:
        stage = GrowthStage(
            season_plan_id=plan.id, name=definition.name, description=definition.description,
            sequence=definition.sequence, start_day=definition.start_day, end_day=definition.end_day,
        )
        db.add(stage)
        stages.append(stage)
    db.flush()
    stage_ids = {stage.sequence: stage.id for stage in stages}
    tasks: list[InitialTaskDefinition] = []
    for item in raw_tasks if isinstance(raw_tasks, list) else []:
        task = InitialTaskDefinition.model_validate(item)
        if task.growth_stage_sequence is not None:
            if task.growth_stage_sequence not in stage_ids:
                raise M2ConflictError("Initial task refers to an unknown growth-stage sequence")
            task.growth_stage_id = stage_ids[task.growth_stage_sequence]
        tasks.append(task)
    db.commit()
    db.refresh(plan)
    return SeasonPlanResponse(
        season_plan_id=plan.id, season_id=plan.season_id, title=plan.title,
        description=plan.description, status=plan.status,
        growth_stages=[GrowthStageDefinition(
            growth_stage_id=stage.id, name=stage.name, description=stage.description,
            sequence=stage.sequence, start_day=stage.start_day, end_day=stage.end_day,
        ) for stage in stages],
        initial_tasks=tasks, created_at=plan.created_at, updated_at=plan.updated_at,
        knowledge_refs=[_knowledge_ref(plan_row)],
    )


def get_season_plan(db: Session, season_id: UUID) -> SeasonPlanResponse:
    season = db.get(Season, season_id)
    if season is None:
        raise M2NotFoundError("Season not found")
    plan = db.scalar(select(SeasonPlan).where(
        SeasonPlan.season_id == season_id,
        SeasonPlan.status.in_(("active", "draft", "completed")),
    ).order_by(SeasonPlan.created_at.desc()).limit(1))
    if plan is None:
        raise M2NotFoundError("Season plan not found")
    stages = list(db.scalars(select(GrowthStage).where(
        GrowthStage.season_plan_id == plan.id
    ).order_by(GrowthStage.sequence)))
    farmland = db.get(Farmland, season.farmland_id)
    if farmland is None:
        raise M2NotFoundError("Farmland not found")
    profile = _season_profile(farmland, season)
    knowledge = _approved_knowledge(
        db, season.crop_id, _farm_today(), season.crop_variety_id,
        _profile_regions(profile), _profile_context(profile, season.planting_date),
        {"season_plan", "crop_calendar"},
    )
    plan_knowledge = _select_season_plan_knowledge(knowledge, season.crop_variety_id)
    raw_tasks = plan_knowledge.content.get("initial_tasks", []) if plan_knowledge else []
    by_sequence = {stage.sequence: stage.id for stage in stages}
    tasks = []
    for item in raw_tasks if isinstance(raw_tasks, list) else []:
        task = InitialTaskDefinition.model_validate(item)
        if task.growth_stage_sequence in by_sequence:
            task.growth_stage_id = by_sequence[task.growth_stage_sequence]
        tasks.append(task)
    return SeasonPlanResponse(
        season_plan_id=plan.id, season_id=season.id, title=plan.title,
        description=plan.description, status=plan.status,
        growth_stages=[GrowthStageDefinition(
            growth_stage_id=stage.id, name=stage.name, description=stage.description,
            sequence=stage.sequence, start_day=stage.start_day, end_day=stage.end_day,
        ) for stage in stages],
        initial_tasks=tasks, created_at=plan.created_at, updated_at=plan.updated_at,
        knowledge_refs=[_knowledge_ref(plan_knowledge)] if plan_knowledge else [],
    )


def get_harvest_guidance(db: Session, season_id: UUID) -> HarvestGuidance:
    season = db.get(Season, season_id)
    if season is None:
        raise M2NotFoundError("Season not found")
    farmland = db.get(Farmland, season.farmland_id)
    if farmland is None:
        raise M2NotFoundError("Farmland not found")
    profile = _season_profile(farmland, season)
    rows = _approved_knowledge(
        db, season.crop_id, _farm_today(), season.crop_variety_id,
        _profile_regions(profile), _profile_context(profile, season.planting_date),
        {"harvest_guidance", "harvest"},
    )
    matching = rows
    matching.sort(key=lambda row: row.crop_variety_id != season.crop_variety_id)
    if not matching:
        raise M2ConflictError("No approved harvest guidance exists for this crop")
    payload = matching[0].content if isinstance(matching[0].content, dict) else {}
    return HarvestGuidance.model_validate({
        **payload,
        "knowledge_refs": [_knowledge_ref(matching[0]).model_dump(mode="json")],
    })


def close_season(db: Session, data: SeasonOutcomeInput) -> SeasonOutcomeResponse:
    season = db.get(Season, data.season_id)
    if season is None:
        raise M2NotFoundError("Season not found")
    if data.actual_harvest_date and season.planting_date and data.actual_harvest_date < season.planting_date:
        raise ValueError("actual_harvest_date must not precede planting_date")
    if data.status not in (None, "completed"):
        raise ValueError("Season close status must be completed")
    if season.status == "cancelled":
        raise M2ConflictError("A cancelled season cannot be closed as harvested")
    if season.status not in {"active", "completed"}:
        raise M2ConflictError("Only active seasons can be closed")
    season.actual_harvest_date = data.actual_harvest_date or season.actual_harvest_date
    season.actual_yield = data.actual_yield if data.actual_yield is not None else season.actual_yield
    season.yield_unit = data.yield_unit if data.yield_unit is not None else season.yield_unit
    season.outcome_notes = data.outcome_notes if data.outcome_notes is not None else season.outcome_notes
    season.status = "completed"
    active_plans = db.scalars(select(SeasonPlan).where(
        SeasonPlan.season_id == season.id, SeasonPlan.status == "active"
    ))
    for plan in active_plans:
        plan.status = "completed"
    db.commit()
    db.refresh(season)
    return SeasonOutcomeResponse(
        season_id=season.id, farmland_id=season.farmland_id, crop_id=season.crop_id,
        crop_variety_id=season.crop_variety_id, planting_date=season.planting_date,
        actual_harvest_date=season.actual_harvest_date, actual_yield=season.actual_yield,
        yield_unit=season.yield_unit, outcome_notes=season.outcome_notes, status=season.status,
    )


def activate_season(db: Session, season_id: UUID) -> SeasonResponse:
    season = db.get(Season, season_id)
    if season is None:
        raise M2NotFoundError("Season not found")
    if season.status == "completed" or season.status == "cancelled":
        raise M2ConflictError("Completed or cancelled seasons cannot be activated")
    plan = db.scalar(select(SeasonPlan).where(
        SeasonPlan.season_id == season.id, SeasonPlan.status == "active"
    ).order_by(SeasonPlan.created_at.desc()))
    if plan is None:
        plan = db.scalar(select(SeasonPlan).where(
            SeasonPlan.season_id == season.id, SeasonPlan.status == "draft"
        ).order_by(SeasonPlan.created_at.desc()))
    if plan is None:
        raise M2ConflictError("Generate a season plan before activation")
    first_stage = db.scalar(select(GrowthStage).where(
        GrowthStage.season_plan_id == plan.id
    ).order_by(GrowthStage.sequence).limit(1))
    if first_stage is None:
        raise M2ConflictError("The season plan has no growth stages")
    other_active = db.scalar(select(Season).where(
        Season.farmland_id == season.farmland_id,
        Season.status == "active",
        Season.id != season.id,
    ))
    if other_active is not None:
        raise M2ConflictError("Another season is already active on this farmland")
    season.status = "active"
    plan.status = "active"
    db.commit()
    db.refresh(season)
    return _season_response(season)
