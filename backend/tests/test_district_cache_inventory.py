"""Availability must not claim missing district data or expose internal paths."""

import socket

from app.core.auth import get_current_farmer_id


def test_inventory_lists_all_districts_without_auth_downloads_or_farm_data(client_and_farm, monkeypatch, tmp_path):
    from app.api import routes_m2_advisor
    client, *_ = client_and_farm
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    monkeypatch.setattr(socket, "create_connection", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("inventory cannot fetch")))
    try:
        response = client.get("/advisory/districts")
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override
    assert response.status_code == 200
    body = response.json()
    assert body["cached_count"] == 0
    assert len(body["districts"]) == 64
    assert body["requires_validation_on_load"] is True
    assert len({item["district_code"] for item in body["districts"]}) == 64
    rajshahi = next(item for item in body["districts"] if item["district_code"] == "5081")
    assert rajshahi["status"] == "missing"
    assert rajshahi["name_bn"] == "রাজশাহী"
    assert "farmland_id" not in response.text and str(tmp_path) not in response.text


def test_inventory_distinguishes_presence_missing_and_unreadable_without_claiming_validity(client_and_farm, monkeypatch, tmp_path):
    from app.api import routes_m2_advisor
    client, *_ = client_and_farm
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    (tmp_path / "5081").mkdir()
    # Presence is deliberately not a scientific validity/availability claim.
    (tmp_path / "5081/bundle.json").write_text("not valid climate data")
    (tmp_path / "3026").mkdir()
    (tmp_path / "3026/bundle.json").mkdir()
    body = client.get("/advisory/districts").json()
    assert body["cached_count"] == 1
    entries = {item["district_code"]: item for item in body["districts"]}
    assert entries["5081"]["status"] == "cached"
    assert entries["3026"]["status"] == "unreadable"
    assert entries["1004"]["status"] == "missing"
    # A selected cached entry must still go through the authoritative reader.
    response = client.get("/advisory", params={"district": "5081", "crop": "rice", "season": "aman"})
    assert response.status_code == 503


def test_inventory_rejects_cache_symlinks_that_escape_root(client_and_farm, monkeypatch, tmp_path):
    from app.api import routes_m2_advisor
    client, *_ = client_and_farm
    root = tmp_path / "cache"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle.json").write_text("private data")
    (root / "5081").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(root))
    response = client.get("/advisory/districts")
    entry = next(item for item in response.json()["districts"] if item["district_code"] == "5081")
    assert entry["status"] == "unreadable"
    assert "private data" not in response.text and str(outside) not in response.text


def test_inventory_does_not_open_indexes_and_marks_oversized_entries_unreadable(client_and_farm, monkeypatch, tmp_path):
    from pathlib import Path
    from app.api import routes_m2_advisor
    from app.services.m1_reference import geography
    client, *_ = client_and_farm
    geography()  # Reference catalog loading is separate from climate-file reads.
    (tmp_path / "5081").mkdir()
    index = tmp_path / "5081/bundle.json"
    with index.open("wb") as stream:
        stream.truncate(2 * 1024 * 1024 + 1)
    monkeypatch.setattr(routes_m2_advisor.settings, "CLIMATE_CACHE_DIR", str(tmp_path))
    original_open = Path.open

    def reject_climate_content_read(path, *args, **kwargs):
        if path.name == "bundle.json":
            raise AssertionError("inventory must not decode/hash daily climate payloads")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", reject_climate_content_read)
    response = client.get("/advisory/districts")
    assert response.status_code == 200
    entries = {item["district_code"]: item for item in response.json()["districts"]}
    assert entries["5081"]["status"] == "unreadable"
    assert response.headers["cache-control"] == "no-store"
