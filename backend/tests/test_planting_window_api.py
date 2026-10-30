"""Authenticated crop-calendar gating for the NASA farmer advisory."""

from app.core.auth import get_current_farmer_id


def test_planting_window_reports_insufficient_data_without_reviewed_calendar(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert "calendar" in body["message_en"]
    assert body["annual_comparison"] is None
    assert body["gdd_summary"] is None
    assert body["data_provenance"]["source"] == "NASA POWER Daily Point"
    assert body["data_provenance"]["spatial_resolution_m"] == 50000
    assert body["data_provenance"]["cache_status"] == "not_requested"


def test_planting_window_hides_other_farmers_seasons(client_and_farm):
    client, _, season_id, _ = client_and_farm
    other_farmland_id = client.app.state.other_farmland_id

    response = client.get(
        f"/advisor/farmlands/{other_farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )

    assert response.status_code == 404


def test_planting_window_requires_authentication(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.get(
            f"/advisor/farmlands/{farmland_id}/planting-window",
            params={"season_id": str(season_id)},
        )
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override

    assert response.status_code == 401
