from pathlib import Path
from uuid import UUID

from app.contracts.challenge.v1 import FarmProfileSnapshot
from app.services.profile_intake.snapshot import FarmSnapshotNotFound

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/foundation/synthetic-golden-farm-snapshot.json"


class FakeFarmProfileSnapshotReader:
    """M1/M3 shared snapshot fake backed by a clearly synthetic golden farm."""

    def __init__(self) -> None:
        self.snapshot = FarmProfileSnapshot.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    def get_snapshot(self, farmer_id: UUID, farmland_id: UUID) -> FarmProfileSnapshot:
        if (farmer_id, farmland_id) != (self.snapshot.farmer_id, self.snapshot.farmland_id):
            raise FarmSnapshotNotFound("farm was not found for this farmer")
        return self.snapshot.model_copy(deep=True)
