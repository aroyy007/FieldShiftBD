"""Published calendars remain references until agronomic execution is reviewed."""

import pytest

from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.models.season import Season


def test_published_calendars_are_public_and_do_not_claim_agronomic_approval(client_and_farm):
    client, _, _, _ = client_and_farm
    farmer_override = client.app.dependency_overrides.pop(get_current_farmer_id)
    try:
        response = client.get("/advisor/calendar-references", params={"crop": "rice"})
    finally:
        client.app.dependency_overrides[get_current_farmer_id] = farmer_override
    assert response.status_code == 200
    profiles = response.json()
    assert {item["season"].casefold() for item in profiles} >= {"aman", "boro", "aus"}
    assert all(item["review_status"] == "source_verified_pending_agronomy_review" for item in profiles)
    assert all(item["activation_allowed"] is False for item in profiles)
    assert all(item["gdd_reference"]["target_degree_days"] is None for item in profiles)
    assert all(item["source_url"].startswith("https://riceprofile.brri.gov.bd/") for item in profiles)


@pytest.mark.parametrize("variety,window", [
    ("BRRI dhan100", {"start": "12-20", "end": "01-10"}),
    ("BRRI dhan48", {"start": "05-01", "end": "05-15"}),
])
def test_saved_variety_gets_published_calendar_without_an_adjusted_advisory(
    client_and_farm, variety, window,
):
    client, farmland_id, season_id, _ = client_and_farm
    dependency = client.app.dependency_overrides[get_db]()
    db = next(dependency)
    db.get(Season, season_id).variety_name = variety
    db.commit()
    dependency.close()

    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["recommended_shift_days"] is None
    reference = body["variety_calendar_reference"]
    assert reference is not None
    assert reference["transplanting_window"] == window
    assert reference["activation_allowed"] is False
    assert reference["gdd_reference"]["status"] == "not_cultivar_validated"


def test_unknown_variety_is_not_assigned_another_varietys_calendar(client_and_farm):
    client, farmland_id, season_id, _ = client_and_farm
    response = client.get(
        f"/advisor/farmlands/{farmland_id}/planting-window",
        params={"season_id": str(season_id)},
    )
    assert response.status_code == 200
    assert response.json()["variety_calendar_reference"] is None


def test_calendar_reference_filters_season_and_rejects_unknown_crop(client_and_farm):
    client, _, _, _ = client_and_farm
    response = client.get("/advisor/calendar-references", params={"crop": "rice", "season": "boro"})
    assert response.status_code == 200
    assert response.json()
    assert all(item["season"].casefold() == "boro" for item in response.json())
    assert client.get("/advisor/calendar-references", params={"crop": "not-a-crop"}).status_code == 422
