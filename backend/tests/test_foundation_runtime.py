import pytest
from fastapi.testclient import TestClient

from app.contracts.challenge.v1 import ApiError
from app.main import app, challenge_unavailable_handler
from app.services.foundation.runtime import (
    ChallengeRuntime,
    ChallengeUnavailable,
    FeatureSwitches,
)


def test_runtime_starts_safe_off_without_adapter_initialization(monkeypatch):
    from app.core.config import settings

    for flag in (
        "CHALLENGE_CLIMATE_ENABLED",
        "CHALLENGE_ADVISORY_ENABLED",
        "CHALLENGE_ROTATION_ENABLED",
        "CHALLENGE_ADAPTIVE_DECISIONS_ENABLED",
        "CHALLENGE_ACTION_CONFIRMATION_ENABLED",
        "CHALLENGE_DISEASE_PROBLEM_SYNC_ENABLED",
        "CHALLENGE_VOICE_ENABLED",
    ):
        monkeypatch.setattr(settings, flag, False)

    runtime = ChallengeRuntime.from_settings(settings)
    assert runtime.adapters == {}
    assert all(not item["enabled"] for item in runtime.availability().values())
    with pytest.raises(ChallengeUnavailable, match="climate"):
        runtime.require_adapter("climate")


def test_enabled_feature_without_installed_provider_is_still_unavailable():
    runtime = ChallengeRuntime(switches=FeatureSwitches(climate=True))
    with pytest.raises(ChallengeUnavailable, match="provider is not installed"):
        runtime.require_adapter("climate")


def test_foundation_availability_endpoint_reports_safe_off_state():
    with TestClient(app) as client:
        response = client.get("/challenge/foundation/availability")

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "1.0.0"
    assert body["features"]["action_confirmation"] == {
        "enabled": False,
        "adapter_ready": False,
    }


def test_disabled_feature_error_is_typed_503():
    import asyncio
    from starlette.requests import Request

    async def invoke():
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
        return await challenge_unavailable_handler(request, ChallengeUnavailable("voice"))

    response = asyncio.run(invoke())
    assert response.status_code == 503
    body = __import__("json").loads(response.body.decode())
    error = ApiError.model_validate(body["detail"])
    assert error.code == "unavailable"
    assert error.details["feature"] == "voice"
