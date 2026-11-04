from datetime import date, datetime, timezone
import importlib.util

import pytest

from app.contracts.challenge.v1 import DistrictClimateBundle, DistrictClimateBundleManifest, DailyClimateObservation


def test_district_publisher_preserves_immutable_version_and_sampling_provenance(tmp_path):
    assert importlib.util.find_spec("app.services.climate.district_publish") is not None
    from app.services.climate.district_publish import publish_district_bundle
    from app.services.climate.cache import ClimateBundleCache
    bundle = DistrictClimateBundle(
        contract_version="1.0.0",
        manifest=DistrictClimateBundleManifest(
            contract_version="1.0.0", district_code="5081", bundle_id="TEST ONLY",
            created_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
            coverage_start=date(2001, 1, 1), coverage_end=date(2001, 1, 1), assets=[],
        ),
        daily_series=[DailyClimateObservation(date=date(2001, 1, 1), rainfall_mm=1, temperature_c=25, solar_mj_m2_day=15)],
    )
    point = {"latitude": 24.37, "longitude": 88.60, "description": "TEST ONLY public point", "source_url": "https://example.invalid/test"}
    path = publish_district_bundle(tmp_path, "5081", bundle, point)
    result = ClimateBundleCache(tmp_path).load_bundle("5081")
    assert result.manifest.sampling_point.description == point["description"]
    assert path.is_file()
    assert list((tmp_path / "5081" / "versions").glob("*.json"))
    original = path.read_bytes()
    bundle.manifest.district_code = "3026"
    with pytest.raises(ValueError, match="district"):
        publish_district_bundle(tmp_path, "5081", bundle, point)
    assert path.read_bytes() == original


def test_publisher_rejects_invalid_district_before_writing(tmp_path):
    assert importlib.util.find_spec("app.services.climate.district_publish") is not None
    from app.services.climate.district_publish import publish_district_bundle
    with pytest.raises(ValueError):
        publish_district_bundle(tmp_path, "../escape", None, {})
    assert list(tmp_path.iterdir()) == []
