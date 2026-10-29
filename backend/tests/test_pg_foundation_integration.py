"""PostgreSQL-only foundation schema and transactional action integration.

Set FIELDSHIFT_PG_TEST_DATABASE_URL to a disposable database ending in
``_test`` and run Alembic to head before executing this suite.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

PG_URL = os.environ.get("FIELDSHIFT_PG_TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not PG_URL, reason="set FIELDSHIFT_PG_TEST_DATABASE_URL to an isolated PostgreSQL test DB"),
]
NOW = datetime(2026, 10, 29, 9, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def pg_sessions():
    database_name = PG_URL.rsplit("/", 1)[-1].split("?", 1)[0]
    if "test" not in database_name.lower():
        pytest.fail("refusing to run foundation integration against a database not named as a test DB")
    engine = create_engine(PG_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar()
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    current_head = ScriptDirectory.from_config(Config(str(alembic_ini))).get_current_head()
    assert version == current_head, "upgrade the isolated PostgreSQL DB with `alembic upgrade head` first"
    yield sessionmaker(autoflush=False, bind=engine)
    engine.dispose()


def _seed(pg_sessions):
    from app.models import Crop, Farmland, Farmer, Season

    with pg_sessions() as db:
        farmer = Farmer(name="SYNTHETIC TEST ONLY", phone_e164=f"+8801{uuid4().int % 10**9:09d}")
        crop = Crop(name=f"SYNTHETIC TEST ONLY {uuid4()}")
        db.add_all([farmer, crop])
        db.flush()
        farm = Farmland(
            farmer_id=farmer.id,
            name="SYNTHETIC TEST ONLY field",
            land_area_sqm=Decimal("1000"),
            land_area_display_unit="square_metre",
        )
        db.add(farm)
        db.flush()
        season = Season(farmland_id=farm.id, crop_id=crop.id, status="active")
        db.add(season)
        db.commit()
        return farmer.id, farm.id, season.id


def test_postgres_migration_creates_only_new_foundation_tables(pg_sessions):
    from app.models import Base

    bind = pg_sessions.kw["bind"]
    actual = set(inspect(bind).get_table_names())
    foundation = {
        "consent_records", "evidence_artifacts", "analysis_records",
        "analysis_record_sources", "adaptive_policy_versions", "proposed_actions",
        "action_receipts", "delivery_outbox",
    }
    assert foundation <= actual
    assert set(Base.metadata.tables) <= actual


def test_postgres_concurrent_confirmation_replays_one_atomic_receipt(pg_sessions):
    from app.contracts.challenge.v1 import ConsentRecordInput, ProposedAction
    from app.models import ActionReceipt, ConsentRecord, DeliveryOutbox, ProposedAction as ActionRow, Task
    from app.services.actions.coordinator import ActionCoordinator
    from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
    from app.services.operational_actions.task_diff import TaskDiffOwnerOperation

    farmer_id, farm_id, season_id = _seed(pg_sessions)

    class NoConflicts:
        def conflicts(self, _db, _proposal):
            return []

    coordinator = ActionCoordinator(
        SQLAlchemyUnitOfWorkFactory(pg_sessions),
        TaskDiffOwnerOperation(),
        NoConflicts(),
        clock=lambda: NOW,
    )
    consent = ConsentRecordInput.model_validate({
            "contract_version": "1.0.0", "purpose": "personalized_advice",
            "decision": "granted", "policy_version": "test-v1",
            "channel": "explicit_tap", "captured_at": NOW.isoformat(),
        })
    consent_key = f"consent-{uuid4()}"
    with ThreadPoolExecutor(max_workers=2) as pool:
        consent_ids = list(pool.map(
            lambda _index: coordinator.record_consent(farmer_id, consent, consent_key), range(2)
        ))
    assert consent_ids[0] == consent_ids[1]
    proposal = ProposedAction.model_validate({
        "contract_version": "1.0.0", "action_id": str(uuid4()),
        "farmer_id": str(farmer_id), "farmland_id": str(farm_id), "season_id": str(season_id),
        "source_module": "m2", "status": "awaiting_confirmation", "version": 1,
        "created_at": NOW.isoformat(), "expires_at": "2026-10-30T09:00:00Z",
        "preconditions": [{"kind": "farm_state_matches", "subject": "season.status"}],
        "task_diff": {"operations": [{"operation": "create", "reference": "synthetic-check", "title": "SYNTHETIC TEST ONLY task"}]},
        "required_consent_purposes": ["personalized_advice"],
    })
    coordinator.propose(proposal)
    key = f"confirm-{uuid4()}"

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(
            lambda _index: coordinator.confirm(farmer_id, proposal.action_id, 1, key), range(2)
        ))

    assert all(receipt.status == "applied" for receipt in receipts)
    assert receipts[0].receipt_id == receipts[1].receipt_id
    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(Task).where(Task.season_id == season_id)) == 1
        assert db.scalar(select(func.count()).select_from(ActionReceipt).where(ActionReceipt.idempotency_key == key)) == 1
        assert db.scalar(
            select(func.count()).select_from(DeliveryOutbox).where(
                DeliveryOutbox.receipt_id == receipts[0].receipt_id
            )
        ) == 1
        assert db.get(ActionRow, proposal.action_id).status == "applied"
        assert db.scalar(select(func.count()).select_from(ConsentRecord).where(ConsentRecord.farmer_id == farmer_id)) == 1

    with pg_sessions.kw["bind"].connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(
                text("UPDATE consent_records SET decision = 'denied' WHERE id = :id"),
                {"id": consent_ids[0]},
            )
        connection.rollback()


def test_postgres_latest_consent_uses_server_version_not_client_capture_time(pg_sessions):
    from datetime import timedelta

    from app.contracts.challenge.v1 import ConsentRecordInput
    from app.models import ConsentRecord
    from app.services.actions.coordinator import ActionCoordinator
    from app.services.actions.uow import SQLAlchemyUnitOfWorkFactory
    from app.services.operational_actions.task_diff import TaskDiffOwnerOperation

    farmer_id, _, _ = _seed(pg_sessions)
    coordinator = ActionCoordinator(
        SQLAlchemyUnitOfWorkFactory(pg_sessions),
        TaskDiffOwnerOperation(),
        precondition_evaluator=type("NoConflicts", (), {"conflicts": lambda *_args: []})(),
        clock=lambda: NOW,
    )
    base = {
        "contract_version": "1.0.0",
        "purpose": "personalized_advice",
        "policy_version": "test-v1",
        "channel": "explicit_tap",
    }
    granted = ConsentRecordInput.model_validate({
        **base, "decision": "granted", "captured_at": NOW.isoformat(),
    })
    backdated_denial = ConsentRecordInput.model_validate({
        **base, "decision": "denied",
        "captured_at": (NOW - timedelta(days=1)).isoformat(),
    })

    coordinator.record_consent(farmer_id, granted, f"consent-grant-{uuid4()}")
    coordinator.record_consent(farmer_id, backdated_denial, f"consent-denial-{uuid4()}")

    with pg_sessions() as db:
        decisions = list(
            db.scalars(
                select(ConsentRecord)
                .where(ConsentRecord.farmer_id == farmer_id)
                .order_by(ConsentRecord.version)
            )
        )
        assert [(record.version, record.decision) for record in decisions] == [
            (1, "granted"), (2, "denied")
        ]
        assert coordinator._missing_consents(
            db, farmer_id, ["personalized_advice"]
        ) == ["personalized_advice"]
