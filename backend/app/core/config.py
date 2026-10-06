from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str
    MODULE3_API_BASE_URL: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: str = "http://localhost:8082,http://127.0.0.1:8082"
    DISEASE_CONFIDENCE_THRESHOLD: float = Field(default=0.70, gt=0, le=1)
    DISEASE_MODEL_WEIGHTS_PATH: str | None = None
    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: float = Field(default=20.0, gt=0, le=60)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
