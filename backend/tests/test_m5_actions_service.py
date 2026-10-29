from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.contracts.challenge.v1 import ProposedAction
from app.models import Crop, Farmer, Farmland, Season, Task
from app.services.m5_actions import FarmActionPreconditionEvaluator


def _farm_state(sessions):
    with sessions() as db:
        farmer = Farmer(name="Synthetic M5 Farmer", phone_e164="+8801700000200")
        crop = Crop(name="Synthetic Aman")
        db.add_all([farmer, crop])
        db.flush()
        farm = Farmland(
            farmer_id=farmer.id,
            name="Synthetic Field",
            land_area_sqm=1000,
            land_area_display_unit="square_metre",
            soil_type="Loam",
        )
        db.add(farm)
        db.flush()
        season = Season(farmland_id=farm.id, crop_id=crop.id, status="active")
        db.add(season)
        db.flush()
        task = Task(
            farmland_id=farm.id,
            season_id=season.id,
            title="Inspect irrigation",
            status="pending",
            priority="normal",
            source="farmer",
        )
        db.add(task)
        db.commit()
        return farmer.id, farm.id, season.id, task.id


def _action(farmer_id, farmland_id, season_id, preconditions, operations=None):
    now = datetime.now(timezone.utc)
    return ProposedAction.model_validate(
        {
            "contract_version": "1.0.0",
            "action_id": str(uuid4()),
            "farmer_id": str(farmer_id),
            "farmland_id": str(farmland_id),
            "season_id": str(season_id),
            "source_module": "m5",
            "status": "awaiting_confirmation",
            "version": 1,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "preconditions": preconditions,
            "task_diff": {"operations": operations or [
                {"operation": "create", "reference": "new-task", "title": "Check field"}
            ]},
        }
    )


def test_farm_state_preconditions_compare_the_current_farm_snapshot(foundation_sessions):
    farmer_id, farmland_id, season_id, _ = _farm_state(foundation_sessions)
    evaluator = FarmActionPreconditionEvaluator()
    now = datetime.now(timezone.utc).isoformat()

    current = _action(farmer_id, farmland_id, season_id, [{
        "kind": "farm_state_matches", "subject": "farmland.soil_type",
        "expected_value": "Loam", "observed_at": now,
    }])
    stale = _action(farmer_id, farmland_id, season_id, [{
        "kind": "farm_state_matches", "subject": "farmland.soil_type",
        "expected_value": "Clay", "observed_at": now,
    }])

    with foundation_sessions() as db:
        assert evaluator.conflicts(db, current) == []
        assert evaluator.conflicts(db, stale) == ["preconditions[0]: farm state changed or subject is unsupported"]


def test_task_and_evidence_preconditions_fail_closed_on_stale_values(foundation_sessions):
    farmer_id, farmland_id, season_id, task_id = _farm_state(foundation_sessions)
    evaluator = FarmActionPreconditionEvaluator()
    now = datetime.now(timezone.utc)
    action = _action(
        farmer_id,
        farmland_id,
        season_id,
        [
            {
                "kind": "evidence_is_fresh",
                "subject": "weather.rainfall",
                "expected_value": 20,
                "observed_at": (now - timedelta(days=3)).isoformat(),
                "max_age_seconds": 3600,
            },
            {"kind": "farm_state_matches", "subject": "farm.unowned_field", "expected_value": True},
        ],
    )

    with foundation_sessions() as db:
        assert evaluator.conflicts(db, action) == [
            "preconditions[0]: evidence is stale or future-dated",
            "preconditions[1]: farm state changed or subject is unsupported",
        ]


def test_task_updates_require_and_recheck_the_complete_snapshot(foundation_sessions):
    farmer_id, farmland_id, season_id, task_id = _farm_state(foundation_sessions)
    evaluator = FarmActionPreconditionEvaluator()
    operation = {
        "operation": "update",
        "reference": "update-task",
        "task_id": str(task_id),
        "expected_status": "pending",
        "title": "Inspect irrigation again",
    }

    with foundation_sessions() as db:
        task = db.get(Task, task_id)
        snapshot = {
            "status": task.status,
            "title": task.title,
            "description": task.description,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "priority": task.priority,
            "updated_at": task.updated_at.isoformat(),
        }

    precondition = {"kind": "task_state_matches", "subject": str(task_id), "expected_value": snapshot}
    action = _action(farmer_id, farmland_id, season_id, [precondition], [operation])
    with foundation_sessions() as db:
        assert evaluator.conflicts(db, action) == []
        task = db.get(Task, task_id)
        task.title = "Renamed by farmer"
        task.updated_at = datetime.now(timezone.utc) + timedelta(seconds=1)
        db.commit()

    with foundation_sessions() as db:
        assert evaluator.conflicts(db, action) == ["preconditions[0]: task snapshot changed"]

    incomplete = _action(
        farmer_id,
        farmland_id,
        season_id,
        [{"kind": "task_state_matches", "subject": str(task_id), "expected_value": "pending"}],
        [operation],
    )
    with foundation_sessions() as db:
        assert evaluator.conflicts(db, incomplete) == [
            "preconditions[0]: a complete task snapshot is required"
        ]


def test_unknown_or_incomplete_evidence_preconditions_do_not_authorize_mutations(foundation_sessions):
    farmer_id, farmland_id, season_id, _ = _farm_state(foundation_sessions)
    evaluator = FarmActionPreconditionEvaluator()
    action = _action(farmer_id, farmland_id, season_id, [{
        "kind": "evidence_is_fresh", "subject": "weather.rainfall", "expected_value": 20,
    }])

    with foundation_sessions() as db:
        assert evaluator.conflicts(db, action) == [
            "preconditions[0]: evidence freshness requirements are incomplete"
        ]
