import base64
import io
import json
from dataclasses import dataclass
from typing import Literal, Protocol, get_args

import httpx
from PIL import Image
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import settings


GeminiFinding = Literal["healthy", "possible_issue", "uncertain", "not_crop"]
GeminiCropMatch = Literal[
    "matches_current_crop",
    "different_crop",
    "uncertain",
]


@dataclass(frozen=True)
class GeminiAssessment:
    finding: GeminiFinding
    crop_match: GeminiCropMatch
    visible_signs: str


class GeminiVerifier(Protocol):
    def verify(self, image: Image.Image, current_crop: str) -> GeminiAssessment:
        ...


class GeminiVerificationError(RuntimeError):
    """Raised when Gemini cannot return a valid image assessment."""


class _GeminiAssessmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    finding: GeminiFinding
    crop_match: GeminiCropMatch
    visible_signs: str


class GeminiApiVerifier:
    """Independent image verifier using Gemini's multimodal Interactions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        timeout_seconds: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.model = model
        self._client = httpx.Client(
            base_url="https://generativelanguage.googleapis.com",
            headers={"x-goog-api-key": api_key},
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def verify(self, image: Image.Image, current_crop: str) -> GeminiAssessment:
        image_buffer = io.BytesIO()
        image.convert("RGB").save(image_buffer, format="JPEG", quality=94, optimize=True)
        prompt = (
            "Independently inspect this crop photo for visual triage. The farm's active crop is "
            + json.dumps(current_crop)
            + ". Do not use any prediction from another model. Choose finding=healthy only if no "
            "visible crop problem is apparent; choose possible_issue for visible signs that may be "
            "disease or pest damage; choose uncertain if the image is insufficient; choose not_crop "
            "if it is not a crop photo. Set crop_match to matches_current_crop, different_crop, or "
            "uncertain. Do not guess a disease from crop identity alone and do not recommend treatment. "
            "In visible_signs, briefly describe only what is visible, or say that it is unclear."
        )
        payload = {
            "model": self.model,
            "input": [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "data": base64.b64encode(image_buffer.getvalue()).decode("ascii"),
                    "mime_type": "image/jpeg",
                },
            ],
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "finding": {
                            "type": "string",
                            "enum": list(get_args(GeminiFinding)),
                        },
                        "crop_match": {
                            "type": "string",
                            "enum": list(get_args(GeminiCropMatch)),
                        },
                        "visible_signs": {"type": "string"},
                    },
                    "required": ["finding", "crop_match", "visible_signs"],
                    "additionalProperties": False,
                },
            },
            "generation_config": {"max_output_tokens": 180, "thinking_level": "low"},
            "store": False,
        }

        try:
            response = self._client.post("/v1/interactions", json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise GeminiVerificationError("Gemini verification is unavailable") from error

        output_text = self._output_text(body)
        if not output_text:
            raise GeminiVerificationError("Gemini returned no assessment")
        try:
            parsed = _GeminiAssessmentPayload.model_validate_json(output_text)
        except (ValidationError, ValueError) as error:
            raise GeminiVerificationError("Gemini returned an invalid assessment") from error

        return GeminiAssessment(
            finding=parsed.finding,
            crop_match=parsed.crop_match,
            visible_signs=parsed.visible_signs[:300],
        )

    @staticmethod
    def _output_text(body: object) -> str | None:
        if not isinstance(body, dict):
            return None
        direct = body.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        chunks: list[str] = []
        steps = body.get("steps")
        if not isinstance(steps, list):
            return None
        for step in steps:
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            content = step.get("content")
            if not isinstance(content, list):
                continue
            chunks.extend(
                item["text"]
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            )
        combined = "".join(chunks).strip()
        return combined or None


def get_gemini_verifier():
    secret = settings.GEMINI_API_KEY
    api_key = secret.get_secret_value().strip() if secret is not None else ""
    if not api_key:
        yield None
        return

    verifier = GeminiApiVerifier(
        api_key=api_key,
        model=settings.GEMINI_MODEL,
        timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
    )
    try:
        yield verifier
    finally:
        verifier.close()
