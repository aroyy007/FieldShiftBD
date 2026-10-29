import pytest

from app.core.config import settings
from app.services.chat_engine import generate_gemini_reply
from app.services.gemini_verification import get_gemini_verifier
from app.services.weather_providers import WeatherProviderError, _http_json


def test_offline_weather_boundary_blocks_direct_provider_http(monkeypatch):
    monkeypatch.setattr(settings, "OFFLINE_MODE", True)

    with pytest.raises(WeatherProviderError, match="outbound weather requests are disabled"):
        _http_json("https://example.invalid/data")


def test_offline_mode_disables_gemini_verifier_even_with_configured_key(monkeypatch):
    from pydantic import SecretStr

    monkeypatch.setattr(settings, "OFFLINE_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr("test-only-not-a-real-key"))

    assert list(get_gemini_verifier()) == [None]


def test_offline_mode_skips_remote_chat_generation(monkeypatch):
    from pydantic import SecretStr

    monkeypatch.setattr(settings, "OFFLINE_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr("test-only-not-a-real-key"))

    assert generate_gemini_reply("system", [], "test") is None
