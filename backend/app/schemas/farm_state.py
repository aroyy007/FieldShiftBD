from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


TaskStatus = Literal["pending", "completed", "skipped", "cancelled"]
TaskSource = Literal["season_plan", "weather", "disease", "farmer", "system"]
TaskPriority = Literal["low", "normal", "high", "urgent"]
TaskScheduleState = Literal[
    "upcoming", "due", "overdue", "unscheduled",
    "completed", "skipped", "cancelled",
]
ProblemStatus = Literal["open", "monitoring", "resolved", "dismissed"]
ProblemSeverity = Literal["low", "moderate", "high", "critical"]
ProblemSource = Literal["farmer", "weather", "disease_detection", "system"]


class PlanTaskInput(BaseModel):
    reference: str = Field(min_length=1, max_length=180)
    growth_stage_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    days_after_planting: int = Field(ge=0)
    priority: TaskPriority = "normal"


class PlanTaskImportRequest(BaseModel):
    tasks: list[PlanTaskInput] = Field(min_length=1)

    @model_validator(mode="after")
    def references_are_unique(self):
        references = [task.reference for task in self.tasks]
        if len(references) != len(set(references)):
            raise ValueError("task references must be unique within an import")
        return self


class TaskCreate(BaseModel):
    season_id: UUID | None = None
    growth_stage_id: UUID | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_at: AwareDatetime | None = None
    priority: TaskPriority = "normal"
    source: TaskSource = "farmer"
    source_reference: str | None = Field(default=None, max_length=200)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    season_id: UUID
    growth_stage_id: UUID | None
    title: str
    description: str | None
    due_at: datetime | None
    status: TaskStatus
    schedule_state: TaskScheduleState = "unscheduled"
    priority: TaskPriority
    source: TaskSource
    source_reference: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskImportResult(BaseModel):
    created_count: int
    existing_count: int
    tasks: list[TaskRead]


class ProblemCreate(BaseModel):
    season_id: UUID | None = None
    source: ProblemSource = "farmer"
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1)
    severity: ProblemSeverity = "moderate"


class ProblemStatusUpdate(BaseModel):
    status: ProblemStatus


class ProblemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    season_id: UUID | None
    source: ProblemSource
    category: str
    description: str
    severity: ProblemSeverity
    status: ProblemStatus
    created_at: datetime
    resolved_at: datetime | None


class CheckinCreate(BaseModel):
    season_id: UUID | None = None
    checkin_at: AwareDatetime | None = None
    growth_stage_id: UUID | None = None
    notes: str | None = None
    observations: dict = Field(default_factory=dict)


class CheckinRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmland_id: UUID
    season_id: UUID | None
    checkin_at: datetime
    growth_stage_id: UUID | None
    notes: str | None
    observations: dict
    created_at: datetime


class GrowthStageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    sequence: int
    start_day: int | None
    end_day: int | None


class ActiveSeasonRead(BaseModel):
    id: UUID
    crop_id: UUID
    crop_name: str
    variety_name: str | None
    planting_date: date | None
    expected_harvest_date: date | None
    status: str


class FarmStateRead(BaseModel):
    farmland_id: UUID
    active_season: ActiveSeasonRead | None
    current_growth_stage: GrowthStageRead | None
    growth_stages: list[GrowthStageRead]
    days_since_planting: int | None
    season_progress_percent: int | None
    tasks: list[TaskRead]
    open_problems: list[ProblemRead]
    latest_checkin: CheckinRead | None


class GrowthStageUpdate(BaseModel):
    growth_stage_id: UUID | None
