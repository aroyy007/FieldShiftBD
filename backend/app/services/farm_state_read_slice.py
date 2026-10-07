"""Read-only Module 3 projection consumed by Module 4 weather assessment."""

from __future__ import annotations

import re
from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Crop, Farmland
from app.models.season import GrowthStage, Season, SeasonPlan
from app.models.state import Task
from app.services.farm_state import FARM_TIMEZONE
from app.services.mock_farm_state import FarmStateSlice, TaskRef


def get_owned_farm_state_slice(
    db: Session, farmland_id: UUID, farmer_id: UUID
) -> FarmStateSlice | None:
    """Build M4's minimal farm-state view from the authenticated farmer's data.

    Returns ``None`` for a missing or foreign farmland so callers can return a
    non-enumerating 404. Coordinates are kept nullable here; the route reports
    a specific 422 when weather cannot be queried without them.
    """
    farmland = db.scalar(
        select(Farmland).where(
            Farmland.id == farmland_id,
            Farmland.farmer_id == farmer_id,
        )
    )
    if farmland is None:
        return None

    season = db.scalar(
        select(Season)
        .where(Season.farmland_id == farmland.id, Season.status == "active")
        .order_by(Season.updated_at.desc())
        .limit(1)
    )

    crop_name = "No active crop"
    growth_stage = "No active stage"
    season_id = None
    stage_id = None
    tasks: list[TaskRef] = []

    if season is not None:
        season_id = season.id
        crop = db.get(Crop, season.crop_id)
        crop_name = crop.name if crop else "Unknown crop"

        if season.current_growth_stage_id is not None:
            active_plan = db.scalar(
                select(SeasonPlan)
                .where(
                    SeasonPlan.season_id == season.id,
                    SeasonPlan.status == "active",
                )
                .order_by(SeasonPlan.updated_at.desc())
                .limit(1)
            )
            if active_plan is not None:
                stage = db.scalar(
                    select(GrowthStage).where(
                        GrowthStage.id == season.current_growth_stage_id,
                        GrowthStage.season_plan_id == active_plan.id,
                    )
                )
                if stage is not None:
                    stage_id = stage.id
                    growth_stage = stage.name

        for task in db.scalars(
            select(Task)
            .where(Task.farmland_id == farmland.id, Task.season_id == season.id)
            .order_by(Task.due_at.is_(None), Task.due_at, Task.created_at)
        ):
            due_date = task.due_at
            if due_date is not None:
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
                due_date = due_date.astimezone(FARM_TIMEZONE)
            tasks.append(
                TaskRef(
                    id=task.id,
                    title=task.title,
                    category=_task_category(task.title, task.description),
                    status=task.status,
                    due_date=due_date.date() if due_date else None,
                    source=task.source,
                )
            )

    location_name = ", ".join(
        value
        for value in (
            farmland.village_or_locality,
            farmland.upazila,
            farmland.district,
            farmland.division,
        )
        if value
    ) or "Unknown location"

    return FarmStateSlice(
        farmland_id=farmland.id,
        season_id=season_id,
        growth_stage_id=stage_id,
        latitude=float(farmland.latitude) if farmland.latitude is not None else None,
        longitude=float(farmland.longitude) if farmland.longitude is not None else None,
        crop_name=crop_name,
        growth_stage=growth_stage,
        location_name=location_name,
        tasks=tasks,
    )


def _task_category(title: str, description: str | None) -> str:
    """Normalize M3's task text into the intent categories M4 suppresses on."""
    text = re.sub(r"\s+", " ", f"{title} {description or ''}").strip().lower()
    categories = (
        ("irrigation", r"\b(irrigat\w*|watering|water the field|water crop)\b"),
        ("spraying", r"\b(spray\w*|pesticide|fungicide|insecticide)\b"),
        ("fertilizing", r"\b(fertili[sz]\w*|top dressing|manure|urea)\b"),
        ("transplanting", r"\b(transplant\w*|planting seedlings)\b"),
        ("harvest", r"\b(harvest\w*)\b"),
    )
    for category, pattern in categories:
        if re.search(pattern, text):
            return category
    return "other"
