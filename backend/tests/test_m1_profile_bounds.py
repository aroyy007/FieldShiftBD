"""Regression coverage for values that exceed the persisted profile schema."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.core.auth import get_current_farmer_id


def test_farmland_create_rejects_area_above_numeric_column_limit(client_and_farm):
    client, _, _, _ = client_and_farm

    response = client.post(
        "/farmlands",
        json={
            "name": "Area above database limit",
            "land_area_sqm": "100000000000",
            "land_area_display_unit": "square_metre",
        },
    )

    assert response.status_code == 422
    assert "land_area_sqm" in str(response.json()["detail"])


def test_farmland_update_rejects_area_above_numeric_column_limit(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    response = client.patch(
        f"/farmlands/{farmland_id}",
        json={"land_area_sqm": "100000000000"},
    )

    assert response.status_code == 422
    current = client.get(f"/farmlands/{farmland_id}")
    assert current.status_code == 200
    assert current.json()["land_area_sqm"] == "1000.000"


def test_farmland_create_accepts_maximum_storable_area(client_and_farm):
    client, _, _, _ = client_and_farm

    response = client.post(
        "/farmlands",
        json={
            "name": "Maximum supported area",
            "land_area_sqm": "99999999999.999",
            "land_area_display_unit": "square_metre",
        },
    )

    assert response.status_code == 201
    assert response.json()["land_area_sqm"] == "99999999999.999"


def test_farmland_create_rejects_unpaired_coordinates(client_and_farm):
    client, _, _, _ = client_and_farm
    non_raising_client = TestClient(client.app, raise_server_exceptions=False)

    response = non_raising_client.post(
        "/farmlands",
        json={"name": "Latitude without longitude", "land_area_sqm": 1000, "latitude": 23.8},
    )

    assert response.status_code == 422


def test_farmland_patch_rejects_unpaired_coordinate_state(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    non_raising_client = TestClient(client.app, raise_server_exceptions=False)

    response = non_raising_client.patch(
        f"/farmlands/{farmland_id}",
        json={"latitude": 23.8},
    )

    assert response.status_code == 422
    current = client.get(f"/farmlands/{farmland_id}")
    assert current.json()["latitude"] is None
    assert current.json()["longitude"] is None


def test_farmland_create_rejects_budget_above_numeric_column_limit(client_and_farm):
    client, _, _, _ = client_and_farm

    response = client.post(
        "/farmlands",
        json={
            "name": "Budget above database limit",
            "land_area_sqm": 1000,
            "budget_amount": "1000000000000",
        },
    )

    assert response.status_code == 422


def test_farmland_create_rejects_yield_above_numeric_column_limit(client_and_farm):
    client, _, _, _ = client_and_farm

    response = client.post(
        "/farmlands",
        json={
            "name": "Yield above database limit",
            "land_area_sqm": 1000,
            "previous_yield_amount": "100000000000",
        },
    )

    assert response.status_code == 422


def test_farmer_profile_rejects_experience_above_numeric_column_limit(client_and_farm):
    client, _, _, _ = client_and_farm
    registered = client.post(
        "/auth/register",
        json={"name": "Bounds test farmer", "phone_e164": "+8801700000002", "password": "correct horse battery"},
    )
    assert registered.status_code == 201
    farmer_id = UUID(registered.json()["farmer_id"])
    client.app.dependency_overrides[get_current_farmer_id] = lambda: farmer_id

    response = client.patch(
        "/profile/farmer-profile",
        json={"farming_experience_years": "1000"},
    )

    assert response.status_code == 422
