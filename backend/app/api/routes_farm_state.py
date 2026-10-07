from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.core import Crop, Farmland
from app.models.season import GrowthStage, Season, SeasonPlan
from app.models.state import FarmCheckin, Problem, Task
from app.schemas.farm_state import (
    ActiveSeasonRead,
    CheckinCreate,
    CheckinRead,
    FarmStateRead,
    GrowthStageRead,
    GrowthStageUpdate,
    PlanTaskImportRequest,
    ProblemCreate,
    ProblemRead,
    ProblemStatus,
    ProblemStatusUpdate,
    TaskCreate,
    TaskImportResult,
    TaskRead,
    TaskScheduleState,
    TaskStatus,
    TaskStatusUpdate,
)
from app.services.farm_state import (
    FARM_TIMEZONE,
    get_season_progress,
    get_task_schedule_state,
    schedule_task_due_at,
)


router = APIRouter(prefix="/farmlands", tags=["Farm State — Module 3"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentFarmerId = Annotated[UUID, Depends(get_current_farmer_id)]


def _get_farmland(db: Session, farmland_id: UUID, farmer_id: UUID) -> Farmland:
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if farmland is None:
        raise HTTPException(status_code=404, detail="Farmland not found")
    return farmland


def _get_season(db: Session, farmland_id: UUID, season_id: UUID) -> Season:
    season = db.scalar(
        select(Season).where(
            Season.id == season_id,
            Season.farmland_id == farmland_id,
        )
    )
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found for this farmland")
    return season


def _get_active_season(db: Session, farmland_id: UUID) -> Season | None:
    return db.scalar(
        select(Season)
        .where(Season.farmland_id == farmland_id, Season.status == "active")
        .order_by(Season.updated_at.desc())
        .limit(1)
    )


def _get_plan(db: Session, season_id: UUID) -> SeasonPlan | None:
    return db.scalar(
        select(SeasonPlan)
        .where(SeasonPlan.season_id == season_id, SeasonPlan.status == "active")
        .order_by(SeasonPlan.updated_at.desc())
        .limit(1)
    )


def _get_plan_stage(
    db: Session, season: Season, growth_stage_id: UUID | None
) -> GrowthStage | None:
    if growth_stage_id is None:
        return None
    plan = _get_plan(db, season.id)
    if plan is None:
        raise HTTPException(status_code=409, detail="Season has no active season plan")
    stage = db.scalar(
        select(GrowthStage).where(
            GrowthStage.id == growth_stage_id,
            GrowthStage.season_plan_id == plan.id,
        )
    )
    if stage is None:
        raise HTTPException(status_code=404, detail="Growth stage not found in season plan")
    return stage


def _task_read(task: Task, as_of: datetime | None = None) -> TaskRead:
    current_time = as_of or datetime.now(timezone.utc)
    return TaskRead.model_validate(task).model_copy(
        update={
            "schedule_state": get_task_schedule_state(
                task.status, task.due_at, current_time
            )
        }
    )


def _checkin_season(
    db: Session, farmland_id: UUID, season_id: UUID | None
) -> Season | None:
    if season_id is not None:
        return _get_season(db, farmland_id, season_id)
    return _get_active_season(db, farmland_id)


def _task_query(db: Session, farmland_id: UUID, season_id: UUID | None = None):
    query = select(Task).where(Task.farmland_id == farmland_id)
    if season_id is not None:
        query = query.where(Task.season_id == season_id)
    return query.order_by(Task.due_at.is_(None), Task.due_at, Task.created_at)


@router.get("/{farmland_id}/state", response_model=FarmStateRead)
def read_farm_state(
    farmland_id: UUID, db: DbSession, farmer_id: CurrentFarmerId
) -> FarmStateRead:
    _get_farmland(db, farmland_id, farmer_id)
    season = _get_active_season(db, farmland_id)
    now = datetime.now(timezone.utc)
    today = now.astimezone(FARM_TIMEZONE).date()

    growth_stages: list[GrowthStage] = []
    current_growth_stage = None
    tasks: list[Task] = []
    active_season = None
    days_since_planting = None
    progress = None

    if season is not None:
        plan = _get_plan(db, season.id)
        if plan is not None:
            growth_stages = list(
                db.scalars(
                    select(GrowthStage)
                    .where(GrowthStage.season_plan_id == plan.id)
                    .order_by(GrowthStage.sequence)
                )
            )
            current_growth_stage = next(
                (
                    stage
                    for stage in growth_stages
                    if stage.id == season.current_growth_stage_id
                ),
                None,
            )

        crop = db.get(Crop, season.crop_id)
        active_season = ActiveSeasonRead(
            id=season.id,
            crop_id=season.crop_id,
            crop_name=crop.name if crop else "Unknown crop",
            variety_name=season.variety_name,
            planting_date=season.planting_date,
            expected_harvest_date=season.expected_harvest_date,
            status=season.status,
        )
        if season.planting_date is not None:
            days_since_planting = max(0, (today - season.planting_date).days)
        progress = get_season_progress(
            season.planting_date, season.expected_harvest_date, today
        )
        tasks = list(
            db.scalars(
                _task_query(db, farmland_id, season.id).limit(200)
            )
        )

    problems = list(
        db.scalars(
            select(Problem)
            .where(Problem.farmland_id == farmland_id, Problem.status.in_(["open", "monitoring"]))
            .order_by(Problem.created_at.desc())
        )
    )
    latest_checkin = db.scalar(
        select(FarmCheckin)
        .where(FarmCheckin.farmland_id == farmland_id)
        .order_by(FarmCheckin.checkin_at.desc(), FarmCheckin.created_at.desc())
        .limit(1)
    )

    return FarmStateRead(
        farmland_id=farmland_id,
        active_season=active_season,
        current_growth_stage=current_growth_stage,
        growth_stages=growth_stages,
        days_since_planting=days_since_planting,
        season_progress_percent=progress,
        tasks=[_task_read(task, now) for task in tasks],
        open_problems=problems,
        latest_checkin=latest_checkin,
    )


@router.get("/{farmland_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    season_id: UUID | None = None,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    schedule_state: TaskScheduleState | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskRead]:
    _get_farmland(db, farmland_id, farmer_id)
    if season_id is not None:
        _get_season(db, farmland_id, season_id)
    query = _task_query(db, farmland_id, season_id)
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
    now = datetime.now(timezone.utc)
    if schedule_state is not None:
        tasks = list(db.scalars(query))
        results = [_task_read(task, now) for task in tasks]
        results = [task for task in results if task.schedule_state == schedule_state]
        return results[offset : offset + limit]
    tasks = list(db.scalars(query.offset(offset).limit(limit)))
    return [_task_read(task, now) for task in tasks]


@router.post("/{farmland_id}/tasks", response_model=TaskRead, status_code=201)
def create_task(
    farmland_id: UUID,
    payload: TaskCreate,
    response: Response,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> TaskRead:
    _get_farmland(db, farmland_id, farmer_id)
    season = (
        _get_season(db, farmland_id, payload.season_id)
        if payload.season_id is not None
        else _get_active_season(db, farmland_id)
    )
    if season is None:
        raise HTTPException(status_code=409, detail="An active season is required to create a task")
    _get_plan_stage(db, season, payload.growth_stage_id)

    if payload.source_reference is not None:
        existing = db.scalar(
            select(Task).where(
                Task.season_id == season.id,
                Task.source_reference == payload.source_reference,
            )
        )
        if existing is not None:
            response.status_code = status.HTTP_200_OK
            return _task_read(existing)

    task = Task(
        farmland_id=farmland_id,
        season_id=season.id,
        growth_stage_id=payload.growth_stage_id,
        title=payload.title.strip(),
        description=payload.description,
        due_at=payload.due_at,
        status="pending",
        priority=payload.priority,
        source=payload.source,
        source_reference=payload.source_reference,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_read(task)


@router.post(
    "/{farmland_id}/seasons/{season_id}/tasks/from-plan",
    response_model=TaskImportResult,
)
def import_plan_tasks(
    farmland_id: UUID,
    season_id: UUID,
    payload: PlanTaskImportRequest,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> TaskImportResult:
    _get_farmland(db, farmland_id, farmer_id)
    season = _get_season(db, farmland_id, season_id)
    if season.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Tasks cannot be imported into a closed season")
    if season.planting_date is None:
        raise HTTPException(status_code=409, detail="Season needs a planting date before tasks can be scheduled")
    plan = _get_plan(db, season.id)
    if plan is None:
        raise HTTPException(status_code=409, detail="Season has no active season plan")

    stages = {
        stage.id: stage
        for stage in db.scalars(
            select(GrowthStage).where(GrowthStage.season_plan_id == plan.id)
        )
    }
    for planned_task in payload.tasks:
        if planned_task.growth_stage_id not in stages:
            raise HTTPException(
                status_code=404,
                detail=f"Growth stage {planned_task.growth_stage_id} not found in season plan",
            )

    references = [f"season-plan:{item.reference}" for item in payload.tasks]
    existing_tasks = list(
        db.scalars(
            select(Task).where(
                Task.season_id == season.id,
                Task.source_reference.in_(references),
            )
        )
    )
    existing_by_reference = {task.source_reference: task for task in existing_tasks}
    created_tasks: list[Task] = []
    for planned_task in payload.tasks:
        source_reference = f"season-plan:{planned_task.reference}"
        if source_reference in existing_by_reference:
            continue
        task = Task(
            farmland_id=farmland_id,
            season_id=season.id,
            growth_stage_id=planned_task.growth_stage_id,
            title=planned_task.title.strip(),
            description=planned_task.description,
            due_at=schedule_task_due_at(
                season.planting_date, planned_task.days_after_planting
            ),
            status="pending",
            priority=planned_task.priority,
            source="season_plan",
            source_reference=source_reference,
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    for task in created_tasks:
        db.refresh(task)
    all_tasks = [*existing_tasks, *created_tasks]
    all_tasks.sort(key=lambda task: (task.due_at is None, task.due_at, task.created_at))
    return TaskImportResult(
        created_count=len(created_tasks),
        existing_count=len(existing_tasks),
        tasks=[_task_read(task) for task in all_tasks],
    )


@router.patch("/{farmland_id}/tasks/{task_id}", response_model=TaskRead)
def update_task_status(
    farmland_id: UUID,
    task_id: UUID,
    payload: TaskStatusUpdate,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> TaskRead:
    _get_farmland(db, farmland_id, farmer_id)
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.farmland_id == farmland_id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found for this farmland")
    task.status = payload.status
    task.completed_at = datetime.now(timezone.utc) if payload.status == "completed" else None
    db.commit()
    db.refresh(task)
    return _task_read(task)


@router.get("/{farmland_id}/tasks/{task_id}", response_model=TaskRead)
def get_task(
    farmland_id: UUID,
    task_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> TaskRead:
    """Get a single task by id, scoped to the authenticated farmer's farmland."""
    _get_farmland(db, farmland_id, farmer_id)
    task = db.scalar(
        select(Task).where(
            Task.id == task_id, Task.farmland_id == farmland_id
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found for this farmland")
    return _task_read(task)


@router.get("/{farmland_id}/problems", response_model=list[ProblemRead])
def list_problems(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    status_filter: Annotated[
        ProblemStatus | None,
        Query(alias="status"),
    ] = None,
) -> list[ProblemRead]:
    _get_farmland(db, farmland_id, farmer_id)
    query = select(Problem).where(Problem.farmland_id == farmland_id)
    if status_filter is not None:
        query = query.where(Problem.status == status_filter)
    problems = db.scalars(query.order_by(Problem.created_at.desc()))
    return [ProblemRead.model_validate(problem) for problem in problems]


@router.post("/{farmland_id}/problems", response_model=ProblemRead, status_code=201)
def create_problem(
    farmland_id: UUID,
    payload: ProblemCreate,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> ProblemRead:
    _get_farmland(db, farmland_id, farmer_id)
    if payload.season_id is not None:
        season = _get_season(db, farmland_id, payload.season_id)
        season_id = season.id
    else:
        active_season = _get_active_season(db, farmland_id)
        season_id = active_season.id if active_season else None
    problem = Problem(
        farmland_id=farmland_id,
        season_id=season_id,
        source=payload.source,
        category=payload.category.strip(),
        description=payload.description.strip(),
        severity=payload.severity,
        status="open",
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return ProblemRead.model_validate(problem)


@router.patch("/{farmland_id}/problems/{problem_id}", response_model=ProblemRead)
def update_problem_status(
    farmland_id: UUID,
    problem_id: UUID,
    payload: ProblemStatusUpdate,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> ProblemRead:
    _get_farmland(db, farmland_id, farmer_id)
    problem = db.scalar(
        select(Problem).where(
            Problem.id == problem_id,
            Problem.farmland_id == farmland_id,
        )
    )
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found for this farmland")
    problem.status = payload.status
    problem.resolved_at = (
        datetime.now(timezone.utc) if payload.status == "resolved" else None
    )
    db.commit()
    db.refresh(problem)
    return ProblemRead.model_validate(problem)


@router.get("/{farmland_id}/problems/{problem_id}", response_model=ProblemRead)
def get_problem(
    farmland_id: UUID,
    problem_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> ProblemRead:
    """Get a single problem by id, scoped to the authenticated farmer's farmland."""
    _get_farmland(db, farmland_id, farmer_id)
    problem = db.scalar(
        select(Problem).where(
            Problem.id == problem_id,
            Problem.farmland_id == farmland_id,
        )
    )
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found for this farmland")
    return ProblemRead.model_validate(problem)


@router.get("/{farmland_id}/check-ins", response_model=list[CheckinRead])
def list_checkins(
    farmland_id: UUID,
    db: DbSession,
    farmer_id: CurrentFarmerId,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CheckinRead]:
    _get_farmland(db, farmland_id, farmer_id)
    checkins = db.scalars(
        select(FarmCheckin)
        .where(FarmCheckin.farmland_id == farmland_id)
        .order_by(FarmCheckin.checkin_at.desc(), FarmCheckin.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [CheckinRead.model_validate(checkin) for checkin in checkins]


@router.post("/{farmland_id}/check-ins", response_model=CheckinRead, status_code=201)
def create_checkin(
    farmland_id: UUID,
    payload: CheckinCreate,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> CheckinRead:
    _get_farmland(db, farmland_id, farmer_id)
    season = _checkin_season(db, farmland_id, payload.season_id)
    if payload.growth_stage_id is not None:
        if season is None:
            raise HTTPException(status_code=409, detail="A season is required for a growth-stage check-in")
        _get_plan_stage(db, season, payload.growth_stage_id)
    checkin = FarmCheckin(
        farmland_id=farmland_id,
        season_id=season.id if season else None,
        checkin_at=payload.checkin_at or datetime.now(timezone.utc),
        growth_stage_id=payload.growth_stage_id,
        notes=payload.notes,
        observations=payload.observations,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return CheckinRead.model_validate(checkin)


@router.patch(
    "/{farmland_id}/state/growth-stage", response_model=GrowthStageRead | None
)
def update_current_growth_stage(
    farmland_id: UUID,
    payload: GrowthStageUpdate,
    db: DbSession,
    farmer_id: CurrentFarmerId,
) -> GrowthStageRead | None:
    _get_farmland(db, farmland_id, farmer_id)
    season = _get_active_season(db, farmland_id)
    if season is None:
        raise HTTPException(status_code=409, detail="Farmland has no active season")
    stage = _get_plan_stage(db, season, payload.growth_stage_id)
    season.current_growth_stage_id = stage.id if stage else None
    db.commit()
    if stage is not None:
        db.refresh(stage)
        return GrowthStageRead.model_validate(stage)
    return None
