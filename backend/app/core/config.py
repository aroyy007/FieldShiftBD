from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    MODULE3_API_BASE_URL: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: str = "http://localhost:8082,http://127.0.0.1:8082"
    DISEASE_CONFIDENCE_THRESHOLD: float = Field(default=0.70, gt=0, le=1)
    DISEASE_MODEL_WEIGHTS_PATH: str | None = None
    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: float = Field(default=20.0, gt=0, le=60)

    @field_validator("SECRET_KEY")
    @classmethod
    def _reject_blank_secret_key(cls, value: str) -> str:
        """Refuse to start with a blank JWT signing key.

        Without this, the app boots normally and every /auth/register and
        /auth/login call dies at runtime with
        ``jwt.exceptions.InvalidKeyError: HMAC key must not be empty``.
        Failing here makes the misconfiguration obvious at deploy time.
        """
        if not value.strip():
            raise ValueError(
                "SECRET_KEY must be set to a non-empty random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
