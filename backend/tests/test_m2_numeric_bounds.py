"""Regression coverage for numeric inputs persisted by Module 2."""


def test_crop_selection_rejects_budget_above_numeric_column_limit(client_and_farm):
    client, farmland_id, _, _ = client_and_farm
    state = client.get(f"/farmlands/{farmland_id}/state").json()
    new_farm = client.post(
        "/farmlands",
        json={"name": "Season budget boundary", "land_area_sqm": 1000},
    )
    assert new_farm.status_code == 201

    response = client.post(
        "/advisor/seasons",
        json={
            "farmland_id": new_farm.json()["id"],
            "crop_id": state["active_season"]["crop_id"],
            "budget_amount": "1000000000000",
        },
    )

    assert response.status_code == 422


def test_season_outcome_rejects_yield_above_numeric_column_limit(client_and_farm):
    client, _, season_id, _ = client_and_farm

    response = client.post(
        f"/advisor/seasons/{season_id}/close",
        json={"season_id": str(season_id), "actual_yield": "100000000000"},
    )

    assert response.status_code == 422
