"""Keep API text limits aligned with the mobile input controls."""


def test_problem_create_rejects_description_over_mobile_limit(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    response = client.post(
        f"/farmlands/{farmland_id}/problems",
        json={
            "source": "farmer",
            "category": "Farmer report",
            "description": "x" * 1001,
            "severity": "moderate",
        },
    )

    assert response.status_code == 422


def test_checkin_create_rejects_notes_over_mobile_limit(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    response = client.post(
        f"/farmlands/{farmland_id}/check-ins",
        json={"notes": "x" * 501},
    )

    assert response.status_code == 422
