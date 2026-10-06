"""Mock Module 3 farm-state read slice for Module 4 development.

M4 is a leaf that depends only on M3's farm state (schema doc section 17:
``farmland_id -> season_id -> farm_state -> tasks/...``). M3 is not implemented
on this branch, so M4 reasons against this *read-only* mock that mirrors the
exact shape M4 needs — and nothing more. When real M3 lands, this module is the
single swap point: replace :func:`get_farm_state_slice` with a call into M3's
read API. M4 must never write farm state (Rule B: suggestions only inside M4).

The slice is deliberately minimal: location (to query weather), current crop +
growth stage (to judge impact), and current/upcoming tasks (what the farmer is
about to do, which is what an alert might change). This is the ``TaskRef`` /
``FarmStateReadSlice`` contract M4 proposes to M3 (see
``docs/m4-contract-proposal.md``).

Golden Farm demo fixture (FARM-001): Rahim, Comilla, Potato, Vegetative stage,
with an irrigation task due tomorrow — the canonical suppression test case.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta

# Stable demo UUIDs so repeated runs/tests reference the same Golden Farm rows.
GOLDEN_FARMLAND_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
GOLDEN_SEASON_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
GOLDEN_GROWTH_STAGE_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")


@dataclass(frozen=True)
class TaskRef:
    """The slice of an M3 ``tasks`` row that M4 needs to reason about impact.

    ``category`` is an M4-internal normalization of the task's intent (e.g.
    ``"irrigation"``, ``"spraying"``, ``"harvest"``) used by suppression rules.
    The team ``tasks`` schema has ``source`` but no ``category`` column, so this
    is derived here and flagged as a Milestone-0 ask to M3 (contract doc).
    """

    id: uuid.UUID
    title: str
    category: str
    status: str          # pending | due | completed | skipped | overdue
    due_date: date | None
    source: str          # season_plan | weather | disease | farmer | system


@dataclass(frozen=True)
class FarmStateSlice:
    """Read-only projection of M3 farm state consumed by the M4 engine."""

    farmland_id: uuid.UUID
    season_id: uuid.UUID | None
    growth_stage_id: uuid.UUID | None
    latitude: float
    longitude: float
    crop_name: str
    growth_stage: str
    location_name: str
    tasks: list[TaskRef] = field(default_factory=list)

    def tasks_in(self, categories: set[str]) -> list[TaskRef]:
        """Active (not completed/skipped) tasks whose category is in ``categories``."""
        return [
            t
            for t in self.tasks
            if t.category in categories and t.status not in {"completed", "skipped"}
        ]


def _golden_farm(*, with_irrigation_task: bool) -> FarmStateSlice:
    tomorrow = date.today() + timedelta(days=1)
    tasks: list[TaskRef] = []
    if with_irrigation_task:
        tasks.append(
            TaskRef(
                id=uuid.UUID("00000000-0000-4000-8000-000000000010"),
                title="Irrigate potato field",
                category="irrigation",
                status="pending",
                due_date=tomorrow,
                source="season_plan",
            )
        )
    return FarmStateSlice(
        farmland_id=GOLDEN_FARMLAND_ID,
        season_id=GOLDEN_SEASON_ID,
        growth_stage_id=GOLDEN_GROWTH_STAGE_ID,
        # Comilla, Bangladesh (demo coordinates; app has no auth, so these are
        # the shared-demo point, not a real farmer's private location).
        latitude=23.46,
        longitude=91.18,
        crop_name="Potato",
        growth_stage="Vegetative",
        location_name="Comilla",
        tasks=tasks,
    )


# Two canonical fixtures for the suppression demo/tests.
_FIXTURES: dict[uuid.UUID, FarmStateSlice] = {
    GOLDEN_FARMLAND_ID: _golden_farm(with_irrigation_task=True),
}


def get_farm_state_slice(farmland_id: uuid.UUID) -> FarmStateSlice | None:
    """Return the mock farm-state slice for ``farmland_id`` (None if unknown).

    Swap point for real M3: replace the dict lookup with an M3 read call.
    """
    return _FIXTURES.get(farmland_id)


def golden_farm_without_irrigation() -> FarmStateSlice:
    """Golden Farm variant with no irrigation task — the suppressed case."""
    return _golden_farm(with_irrigation_task=False)


def golden_farm_with_irrigation() -> FarmStateSlice:
    """Golden Farm variant with an irrigation task due tomorrow — the alert case."""
    return _golden_farm(with_irrigation_task=True)
