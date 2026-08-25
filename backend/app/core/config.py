"""Core application configuration via Pydantic Settings."""

import json
from typing import Annotated, Any

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(v: Any) -> list[str]:
    """Parse CORS origins from JSON string, comma-separated string, or list."""
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed]
            except Exception:
                pass
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    elif isinstance(v, (list, tuple)):
        return [str(item).strip() for item in v]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


class Settings(BaseSettings):
    """Application settings with environment variable override."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project Information
    PROJECT_NAME: str = "METFI Autonomous Finance Controller"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server & API
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors_origins)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://metfi_admin:metfi_secure_password@localhost:5432/metfi_reconciliation"
    )

    # AI Configuration
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_AI_MODEL: str = "gemini-2.5-pro"

    # Engine Defaults
    DEFAULT_BENCHMARK_SEED: int = 42


settings = Settings()
