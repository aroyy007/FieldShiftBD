"""Dependency-free, safe-off feature composition.

Importing this module performs no I/O. Real providers are injected by the
module integration owner only after their feature's readiness gates pass.
"""

from dataclasses import dataclass, field
from typing import Any


class ChallengeUnavailable(RuntimeError):
    def __init__(self, feature: str, message: str | None = None):
        self.feature = feature
        super().__init__(message or f"The {feature} capability is currently unavailable.")


@dataclass(frozen=True)
class FeatureSwitches:
    climate: bool = False
    advisory: bool = False
    rotation: bool = False
    adaptive_decisions: bool = False
    action_confirmation: bool = False
    disease_problem_sync: bool = False
    voice: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "climate": self.climate,
            "advisory": self.advisory,
            "rotation": self.rotation,
            "adaptive_decisions": self.adaptive_decisions,
            "action_confirmation": self.action_confirmation,
            "disease_problem_sync": self.disease_problem_sync,
            "voice": self.voice,
        }


@dataclass
class ChallengeRuntime:
    """Application-scoped feature flags and injectable module adapters."""

    switches: FeatureSwitches = field(default_factory=FeatureSwitches)
    adapters: dict[str, Any] = field(default_factory=dict)
    offline_mode: bool = False

    @classmethod
    def from_settings(cls, settings: Any) -> "ChallengeRuntime":
        return cls(
            switches=FeatureSwitches(
                climate=settings.CHALLENGE_CLIMATE_ENABLED,
                advisory=settings.CHALLENGE_ADVISORY_ENABLED,
                rotation=settings.CHALLENGE_ROTATION_ENABLED,
                adaptive_decisions=settings.CHALLENGE_ADAPTIVE_DECISIONS_ENABLED,
                action_confirmation=settings.CHALLENGE_ACTION_CONFIRMATION_ENABLED,
                disease_problem_sync=settings.CHALLENGE_DISEASE_PROBLEM_SYNC_ENABLED,
                voice=settings.CHALLENGE_VOICE_ENABLED,
            ),
            # Deliberately empty. No provider or model initializes on import.
            adapters={},
            offline_mode=settings.OFFLINE_MODE,
        )

    def is_enabled(self, feature: str) -> bool:
        return bool(getattr(self.switches, feature, False))

    def require_adapter(self, feature: str, adapter_name: str | None = None) -> Any:
        if not self.is_enabled(feature):
            raise ChallengeUnavailable(feature)
        key = adapter_name or feature
        adapter = self.adapters.get(key)
        if adapter is None:
            raise ChallengeUnavailable(feature, f"The {feature} provider is not installed.")
        return adapter

    def availability(self) -> dict[str, dict[str, bool]]:
        switches = self.switches.as_dict()
        return {
            name: {"enabled": enabled, "adapter_ready": name in self.adapters}
            for name, enabled in switches.items()
        }
