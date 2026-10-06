import os

from fastapi.testclient import TestClient

os.environ.update(
    {
        "DB_USER": "fieldshift_test",
        "DB_PASSWORD": "fieldshift_test",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "fieldshift_test",
        "DATABASE_URL": "sqlite://",
    }
)

from app.main import app


def test_local_expo_web_origin_can_call_backend_api():
    response = TestClient(app).options(
        "/advisor/recommendations",
        headers={
            "Origin": "http://localhost:8082",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8082"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_unconfigured_web_origin_is_not_allowed():
    response = TestClient(app).options(
        "/advisor/recommendations",
        headers={
            "Origin": "https://unconfigured.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
