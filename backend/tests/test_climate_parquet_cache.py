"""The disk codec must preserve scientific values and reject mixed/corrupt releases."""

from datetime import date, datetime, timezone
import hashlib
import json
import socket

import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from app.contracts.challenge.v1 import (
    DailyClimateObservation, DistrictClimateBundle, DistrictClimateBundleManifest,
)
from app.services.climate.cache import ClimateBundleCache, CorruptClimateCache
from app.services.climate.district_publish import publish_district_bundle

POINT = {"latitude": 24.37, "longitude": 88.70, "description": "SYNTHETIC TEST ONLY point",
         "source_url": "https://example.invalid/synthetic-point"}


def daily_bundle():
    return DistrictClimateBundle(
        contract_version="1.0.0",
        manifest=DistrictClimateBundleManifest(
            contract_version="1.0.0", district_code="5081", bundle_id="SYNTHETIC TEST ONLY",
            created_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
            coverage_start=date(2001, 1, 1), coverage_end=date(2001, 1, 3),
            assets=[], quality_status="synthetic",
        ),
        daily_series=[
            DailyClimateObservation(date=date(2001, 1, 1), rainfall_mm=0,
                                    temperature_c=-2.5, solar_mj_m2_day=8.68),
            DailyClimateObservation(date=date(2001, 1, 3), rainfall_mm=4.25,
                                    temperature_c=24.2, solar_mj_m2_day=12.5,
                                    quality_flags=["SYNTHETIC", "gap-before"]),
        ],
    )


def test_publication_writes_parquet_and_reader_preserves_units_gaps_and_flags(tmp_path, monkeypatch):
    source = daily_bundle()
    target = publish_district_bundle(tmp_path, "5081", source, POINT)
    index = json.loads(target.read_bytes())
    assert index.get("cache_format") == "fieldshift-climate-parquet-v1"
    assert "daily_series" not in index
    assert index["daily_series_row_count"] == 2
    asset = next(item for item in index["manifest"]["assets"] if item["asset_id"] == index["daily_series_asset_id"])
    payload = (tmp_path / asset["relative_path"]).read_bytes()
    assert payload[:4] == payload[-4:] == b"PAR1"
    assert hashlib.sha256(payload).hexdigest() == asset["checksum_sha256"]
    monkeypatch.setattr(socket, "socket", lambda *_a, **_kw: pytest.fail("local cache used network"))
    result = ClimateBundleCache(tmp_path).load_bundle("5081")
    assert [row.model_dump(mode="json") for row in result.daily_series] == [
        {"date": "2001-01-01", "rainfall_mm": 0.0, "temperature_c": -2.5,
         "solar_mj_m2_day": 8.68, "quality_flags": []},
        {"date": "2001-01-03", "rainfall_mm": 4.25, "temperature_c": 24.2,
         "solar_mj_m2_day": 12.5, "quality_flags": ["SYNTHETIC", "gap-before"]},
    ]
    assert source.manifest.assets == [] and source.manifest.sampling_point is None


def test_new_publication_retains_old_index_and_parquet_asset(tmp_path):
    bundle = daily_bundle()
    target = publish_district_bundle(tmp_path, "5081", bundle, POINT)
    first = json.loads(target.read_bytes())
    assert first.get("cache_format") == "fieldshift-climate-parquet-v1"
    old_bytes = target.read_bytes()
    old_assets = {p: (tmp_path / p).read_bytes() for p in [item["relative_path"] for item in first["manifest"]["assets"]]}
    bundle.daily_series[0].rainfall_mm = 9
    publish_district_bundle(tmp_path, "5081", bundle, POINT)
    assert target.read_bytes() != old_bytes
    assert any(p.read_bytes() == old_bytes for p in (tmp_path / "5081/versions").glob("*.json"))
    assert all((tmp_path / p).read_bytes() == payload for p, payload in old_assets.items())
    assert ClimateBundleCache(tmp_path).load_bundle("5081").daily_series[0].rainfall_mm == 9


def test_first_parquet_publication_preserves_the_previous_inline_json_index(tmp_path):
    bundle = daily_bundle()
    district_dir = tmp_path / "5081"
    district_dir.mkdir()
    target = district_dir / "bundle.json"
    previous_index = bundle.model_dump_json().encode("utf-8")
    target.write_bytes(previous_index)

    publish_district_bundle(tmp_path, "5081", bundle, POINT)

    previous_hash = hashlib.sha256(previous_index).hexdigest()
    archived = district_dir / "versions" / f"{previous_hash}.json"
    assert archived.read_bytes() == previous_index


def test_publisher_refuses_to_reuse_a_corrupt_content_addressed_parquet_file(tmp_path):
    bundle = daily_bundle()
    target = publish_district_bundle(tmp_path, "5081", bundle, POINT)
    index_before = target.read_bytes()
    index = json.loads(index_before)
    asset = next(item for item in index["manifest"]["assets"]
                 if item["asset_id"] == index["daily_series_asset_id"])
    (tmp_path / asset["relative_path"]).write_bytes(b"corrupted immutable asset")

    with pytest.raises(ValueError, match="immutable cache file"):
        publish_district_bundle(tmp_path, "5081", bundle, POINT)

    assert target.read_bytes() == index_before


def test_parquet_index_cannot_override_rows_with_an_inline_copy(tmp_path):
    target = publish_district_bundle(tmp_path, "5081", daily_bundle(), POINT)
    index = json.loads(target.read_bytes())
    # Legacy readers accept an inline-only bundle. New-format metadata must
    # never be ignored in favour of an unverified alternate representation.
    index.update(cache_format="fieldshift-climate-parquet-v1", daily_series_asset_id="missing",
                 daily_series_row_count=2)
    index["daily_series"] = [row.model_dump(mode="json") for row in daily_bundle().daily_series]
    target.write_text(json.dumps(index))
    with pytest.raises(CorruptClimateCache):
        ClimateBundleCache(tmp_path).load_bundle("5081")


def test_parquet_row_count_mismatch_is_not_silently_returned(tmp_path):
    target = publish_district_bundle(tmp_path, "5081", daily_bundle(), POINT)
    index = json.loads(target.read_bytes())
    assert index.get("cache_format") == "fieldshift-climate-parquet-v1"
    index["daily_series_row_count"] = 1
    target.write_text(json.dumps(index))
    with pytest.raises(CorruptClimateCache, match="row count"):
        ClimateBundleCache(tmp_path).load_bundle("5081")


def test_damaged_parquet_bytes_fail_checksum_validation(tmp_path):
    target = publish_district_bundle(tmp_path, "5081", daily_bundle(), POINT)
    index = json.loads(target.read_bytes())
    assert index.get("cache_format") == "fieldshift-climate-parquet-v1"
    asset = next(item for item in index["manifest"]["assets"] if item["asset_id"] == index["daily_series_asset_id"])
    path = tmp_path / asset["relative_path"]
    path.write_bytes(b"X" * len(path.read_bytes()))
    with pytest.raises(CorruptClimateCache, match="checksum"):
        ClimateBundleCache(tmp_path).load_bundle("5081")


def test_parquet_schema_is_validated_even_when_asset_checksum_is_updated(tmp_path):
    target = publish_district_bundle(tmp_path, "5081", daily_bundle(), POINT)
    index = json.loads(target.read_bytes())
    asset = next(item for item in index["manifest"]["assets"]
                 if item["asset_id"] == index["daily_series_asset_id"])
    path = tmp_path / asset["relative_path"]
    wrong_schema = pa.schema([
        pa.field("date", pa.date32()),
        pa.field("rainfall_mm", pa.float64()),
        pa.field("temperature_c", pa.float64()),
        pa.field("solar_mj_m2_day", pa.float64()),
        pa.field("quality_flags", pa.string()),
    ])
    table = pa.Table.from_pylist([
        {"date": date(2001, 1, 1), "rainfall_mm": 1.0, "temperature_c": 25.0,
         "solar_mj_m2_day": 10.0, "quality_flags": "SYNTHETIC"},
        {"date": date(2001, 1, 2), "rainfall_mm": 2.0, "temperature_c": 26.0,
         "solar_mj_m2_day": 11.0, "quality_flags": "SYNTHETIC"},
    ], schema=wrong_schema)
    output = pa.BufferOutputStream()
    pq.write_table(table, output)
    payload = output.getvalue().to_pybytes()
    path.write_bytes(payload)
    asset["checksum_sha256"] = hashlib.sha256(payload).hexdigest()
    asset["size_bytes"] = len(payload)
    target.write_text(json.dumps(index))

    with pytest.raises(CorruptClimateCache, match="schema"):
        ClimateBundleCache(tmp_path).load_bundle("5081")


def test_parquet_reader_enforces_asset_byte_limit(tmp_path):
    target = publish_district_bundle(tmp_path, "5081", daily_bundle(), POINT)
    index = json.loads(target.read_bytes())
    asset = next(item for item in index["manifest"]["assets"]
                 if item["asset_id"] == index["daily_series_asset_id"])
    with pytest.raises(CorruptClimateCache, match="asset exceeds"):
        ClimateBundleCache(tmp_path, max_asset_bytes=asset["size_bytes"] - 1).load_bundle("5081")
