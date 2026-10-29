from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.main import app
from app.models import Base, Crop, Farmer, Farmland, Season, Task
from app.services.actions.coordinator import ActionCoordinator
from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
from app.services.foundation.runtime import FeatureSwitches
from app.services.m5_actions import FarmActionPreconditionEvaluator
from app.services.operational_actions.task_diff import TaskDiffOwnerOperation


def _proposal(farmer_id, farmland_id, season_id, *, soil_type=None):
    now = datetime.now(timezone.utc)
    preconditions = [{
        "kind": "farm_state_matches",
        "subject": "season.status",
        "expected_value": "active",
        "observed_at": now.isoformat(),
    }]
    if soil_type is not None:
        preconditions.append({
            "kind": "farm_state_matches",
            "subject": "farmland.soil_type",
            "expected_value": soil_type,
            "observed_at": now.isoformat(),
        })
    return {
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
        "task_diff": {
            "operations": [{
                "operation": "create",
                "reference": f"m5-task-{uuid4()}",
                "title": "Review field drainage",
                "priority": "normal",
            }]
        },
        "required_consent_purposes": [],
    }


def test_m5_action_http_flow_persists_proposal_applies_once_and_rejects_stale_farm_state(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'm5-actions.db'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_transactions(connection, _record):
        connection.isolation_level = None
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    @event.listens_for(engine, "begin")
    def begin_sqlite_transaction(connection):
        connection.exec_driver_sql("BEGIN")

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is None:
                continue
            default_sql = str(column.server_default.arg)
            if "gen_random_uuid" in default_sql or "::jsonb" in default_sql:
                column.server_default = None

    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(autoflush=False, expire_on_commit=False, bind=engine)

    with test_sessions() as db:
        farmer = Farmer(name="Synthetic Action Farmer", phone_e164="+8801700000300")
        crop = Crop(name="Synthetic Aman")
        db.add_all([farmer, crop])
        db.flush()
        farmland = Farmland(
            farmer_id=farmer.id,
            name="Synthetic South Field",
            land_area_sqm=1000,
            land_area_display_unit="square_metre",
            soil_type="Loam",
        )
        db.add(farmland)
        db.flush()
        season = Season(farmland_id=farmland.id, crop_id=crop.id, status="active")
        db.add(season)
        db.commit()
        farmer_id, farmland_id, season_id = farmer.id, farmland.id, season.id
        task = Task(
            farmland_id=farmland_id,
            season_id=season_id,
            title="Inspect irrigation",
            status="pending",
            priority="normal",
            source="farmer",
        )
        db.add(task)
        db.commit()
        task_id = task.id

    coordinator = ActionCoordinator(
        SQLAlchemyUnitOfWorkFactory(test_sessions),
        TaskDiffOwnerOperation(),
        FarmActionPreconditionEvaluator(),
    )
    previous_runtime = app.state.challenge_runtime
    previous_overrides = dict(app.dependency_overrides)
    app.state.challenge_runtime = previous_runtime.__class__(
        switches=FeatureSwitches(action_confirmation=True),
        adapters={"action_confirmation": coordinator},
    )

    def override_db():
        with test_sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_farmer_id] = lambda: farmer_id
    try:
        with TestClient(app) as client:
            proposal_body = _proposal(farmer_id, farmland_id, season_id)
            proposal_response = client.post(
                f"/farmlands/{farmland_id}/actions/proposals", json=proposal_body
            )
            assert proposal_response.status_code == 201
            action_id = proposal_response.json()["action_id"]
            assert len(client.get(f"/farmlands/{farmland_id}/actions/pending").json()) == 1

            confirm_body = {
                "expected_version": 1,
                "idempotency_key": "m5-action-confirm-0001",
                "decision": "confirm",
            }
            first = client.post(
                f"/farmlands/{farmland_id}/actions/{action_id}/confirm", json=confirm_body
            )
            replay = client.post(
                f"/farmlands/{farmland_id}/actions/{action_id}/confirm", json=confirm_body
            )
            assert first.status_code == replay.status_code == 200
            assert first.json()["status"] == "applied"
            assert replay.json()["receipt_id"] == first.json()["receipt_id"]
            assert client.get(f"/farmlands/{farmland_id}/actions/pending").json() == []

            stale_body = _proposal(farmer_id, farmland_id, season_id, soil_type="Loam")
            stale_proposal = client.post(
                f"/farmlands/{farmland_id}/actions/proposals", json=stale_body
            )
            assert stale_proposal.status_code == 201
            with test_sessions() as db:
                farm = db.get(Farmland, farmland_id)
                farm.soil_type = "Clay"
                db.commit()

            stale_action_id = stale_proposal.json()["action_id"]
            stale_result = client.post(
                f"/farmlands/{farmland_id}/actions/{stale_action_id}/confirm",
                json={
                    "expected_version": 1,
                    "idempotency_key": "m5-action-stale-0001",
                    "decision": "confirm",
                },
            )
            assert stale_result.status_code == 200
            assert stale_result.json()["status"] == "conflict"
            assert stale_result.json()["result"]["code"] == "precondition_changed"

            with test_sessions() as db:
                task = db.get(Task, task_id)
                task_snapshot = {
                    "status": task.status,
                    "title": task.title,
                    "description": task.description,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                    "priority": task.priority,
                    "updated_at": task.updated_at.isoformat(),
                }
                task.title = "Changed by farmer"
                task.updated_at = datetime.now(timezone.utc)
                db.commit()

            stale_task_body = _proposal(farmer_id, farmland_id, season_id)
            stale_task_body["preconditions"] = [{
                "kind": "task_state_matches",
                "subject": str(task_id),
                "expected_value": task_snapshot,
            }]
            stale_task_body["task_diff"]["operations"] = [{
                "operation": "update",
                "reference": "stale-update-task-title",
                "task_id": str(task_id),
                "expected_status": "pending",
                "title": "Overwritten by M5",
            }]
            stale_task_response = client.post(
                f"/farmlands/{farmland_id}/actions/proposals", json=stale_task_body
            )
            assert stale_task_response.status_code == 201
            stale_task_id = stale_task_response.json()["action_id"]
            stale_task_result = client.post(
                f"/farmlands/{farmland_id}/actions/{stale_task_id}/confirm",
                json={
                    "expected_version": 1,
                    "idempotency_key": "m5-stale-task-0001",
                    "decision": "confirm",
                },
            )
            assert stale_task_result.status_code == 200
            assert stale_task_result.json()["status"] == "conflict"
            assert stale_task_result.json()["result"]["code"] == "precondition_changed"
            with test_sessions() as db:
                assert db.get(Task, task_id).title == "Changed by farmer"

            with test_sessions() as db:
                task = db.get(Task, task_id)
                current_snapshot = {
                    "status": task.status,
                    "title": task.title,
                    "description": task.description,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                    "priority": task.priority,
                    "updated_at": task.updated_at.isoformat(),
                }
            complete_body = _proposal(farmer_id, farmland_id, season_id)
            complete_body["preconditions"] = [{
                "kind": "task_state_matches",
                "subject": str(task_id),
                "expected_value": current_snapshot,
            }]
            complete_body["task_diff"]["operations"] = [{
                "operation": "complete",
                "reference": "complete-task-with-contract-default",
                "task_id": str(task_id),
            }]
            complete_proposal = client.post(
                f"/farmlands/{farmland_id}/actions/proposals", json=complete_body
            )
            assert complete_proposal.status_code == 201
            assert complete_proposal.json()["task_diff"]["operations"][0]["expected_status"] == "pending"
            complete_action_id = complete_proposal.json()["action_id"]
            pending = client.get(f"/farmlands/{farmland_id}/actions/pending").json()
            assert len(pending) == 1
            assert pending[0]["action_id"] == complete_action_id
            assert pending[0]["task_diff"]["operations"][0]["expected_status"] == "pending"
            complete_result = client.post(
                f"/farmlands/{farmland_id}/actions/{complete_action_id}/confirm",
                json={
                    "expected_version": 1,
                    "idempotency_key": "m5-complete-task-0001",
                    "decision": "confirm",
                },
            )
            assert complete_result.status_code == 200
            assert complete_result.json()["status"] == "applied"
            with test_sessions() as db:
                assert db.get(Task, task_id).status == "completed"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        app.state.challenge_runtime = previous_runtime
        Base.metadata.drop_all(engine)
        engine.dispose()
