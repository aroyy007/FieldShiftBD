from datetime import date

from app.api import routes_m4_weather


def test_weather_assessment_uses_the_owned_farm_state(client_and_farm, monkeypatch):
    client, farmland_id, season_id, stage_id = client_and_farm
    location = client.patch(
        f"/farmlands/{farmland_id}",
        json={"latitude": 23.81, "longitude": 90.41, "district": "Gazipur"},
    )
    assert location.status_code == 200

    task = client.post(
        f"/farmlands/{farmland_id}/tasks",
        json={
            "season_id": str(season_id),
            "growth_stage_id": str(stage_id),
            "title": "Irrigate rice field",
            "source": "farmer",
        },
    )
    assert task.status_code == 201

    requested_coordinates = []

    def fake_fetch_weather(latitude, longitude):
        requested_coordinates.append((latitude, longitude))
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "forecast": {
                "state": "available",
                "data": {
                    "daily": [
                        {
                            "date": date.today().isoformat(),
                            "precipitation_mm": 60,
                            "temperature_max_c": 30,
                            "wind_speed_max_kmh": 10,
                        }
                    ]
                },
            },
            "nasa_power": {"state": "unavailable", "reason": "test"},
        }

    monkeypatch.setattr(routes_m4_weather, "fetch_weather", fake_fetch_weather)
    response = client.get(f"/weather/assessment/{farmland_id}")

    assert response.status_code == 200
    body = response.json()
    assert requested_coordinates == [(23.81, 90.41)]
    assert body["farmland_id"] == str(farmland_id)
    assert body["crop_name"] == "Rice"
    assert body["growth_stage"] == "Vegetative"
    assert body["location_name"] == "Gazipur"
    assert body["alerts"][0]["triggering_task_titles"] == ["Irrigate rice field"]


def test_weather_assessment_requires_coordinates_for_the_owned_farm(client_and_farm):
    client, farmland_id, _, _ = client_and_farm

    response = client.get(f"/weather/assessment/{farmland_id}")

    assert response.status_code == 422
    assert response.json()["detail"] == "Farmland coordinates are required for a weather assessment."


def test_weather_assessment_does_not_expose_another_farmers_location(client_and_farm):
    client, _, _, _ = client_and_farm
    other_farmland_id = client.app.state.other_farmland_id

    response = client.get(f"/weather/assessment/{other_farmland_id}")

    assert response.status_code == 404


def test_weather_assessment_suppresses_work_for_a_cancelled_task(client_and_farm, monkeypatch):
    client, farmland_id, season_id, stage_id = client_and_farm
    client.patch(
        f"/farmlands/{farmland_id}",
        json={"latitude": 23.81, "longitude": 90.41},
    )
    task = client.post(
        f"/farmlands/{farmland_id}/tasks",
        json={
            "season_id": str(season_id),
            "growth_stage_id": str(stage_id),
            "title": "Irrigate rice field",
            "source": "farmer",
        },
    ).json()
    cancelled = client.patch(
        f"/farmlands/{farmland_id}/tasks/{task['id']}",
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200

    monkeypatch.setattr(
        routes_m4_weather,
        "fetch_weather",
        lambda latitude, longitude: {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "forecast": {
                "state": "available",
                "data": {
                    "daily": [
                        {
                            "date": date.today().isoformat(),
                            "precipitation_mm": 60,
                        }
                    ]
                },
            },
            "nasa_power": {"state": "unavailable", "reason": "test"},
        },
    )

    response = client.get(f"/weather/assessment/{farmland_id}")

    assert response.status_code == 200
    assert response.json()["alerts"] == []
    assert response.json()["suppressed_events"][0]["event_type"] == "heavy_rain"
