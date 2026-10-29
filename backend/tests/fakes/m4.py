from datetime import date, datetime, timezone
from enum import Enum

from app.contracts.challenge.ports import AdapterConflict, AdapterUnavailable, ArtifactNotFound, StaleArtifact
from app.contracts.challenge.v1 import DistrictClimateBundle


class FakeClimateScenario(str, Enum):
    SUPPORTED = "supported"
    UNKNOWN = "unknown"
    EXPIRED = "expired"
    CONFLICT = "conflict"
    FAILURE = "failure"


class FakeDistrictClimateBundleProvider:
    def __init__(self, scenario=FakeClimateScenario.SUPPORTED):
        self.scenario = FakeClimateScenario(scenario)
        self.requests = []

    def get_bundle(self, district_code, *, as_of):
        self.requests.append((district_code, as_of))
        if self.scenario is FakeClimateScenario.UNKNOWN:
            raise ArtifactNotFound("synthetic unknown district")
        if self.scenario is FakeClimateScenario.EXPIRED:
            raise StaleArtifact("synthetic expired climate bundle")
        if self.scenario is FakeClimateScenario.CONFLICT:
            raise AdapterConflict("synthetic district/version conflict")
        if self.scenario is FakeClimateScenario.FAILURE:
            raise AdapterUnavailable("synthetic adapter failure")
        return DistrictClimateBundle(
            contract_version="1.0.0",
            manifest={
                "contract_version": "1.0.0",
                "district_code": district_code,
                "bundle_id": "synthetic-test-bundle-v1",
                "created_at": datetime(2026, 10, 28, tzinfo=timezone.utc),
                "expires_at": datetime(2026, 10, 30, tzinfo=timezone.utc),
                "coverage_start": date(2026, 10, 1),
                "coverage_end": date(2026, 10, 1),
                "assets": [],
                "provenance": [],
                "quality_status": "synthetic",
            },
            daily_series=[
                {
                    "date": date(2026, 10, 1),
                    "rainfall_mm": 4.2,
                    "temperature_c": 28.1,
                    "solar_mj_m2_day": 18.0,
                }
            ],
        )
