"""Unit tests for configuration loading and parsing."""

from app.core.config import Settings, parse_cors_origins


def test_parse_cors_origins_json() -> None:
    """Verify JSON array parsing for CORS origins."""
    raw = '["http://localhost:3000", "https://app.metfi.ai"]'
    parsed = parse_cors_origins(raw)
    assert parsed == ["http://localhost:3000", "https://app.metfi.ai"]


def test_parse_cors_origins_csv() -> None:
    """Verify comma-separated string parsing for CORS origins."""
    raw = "http://localhost:3000, http://127.0.0.1:3000"
    parsed = parse_cors_origins(raw)
    assert parsed == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_default_settings() -> None:
    """Verify default settings configuration."""
    settings = Settings()
    assert settings.PROJECT_NAME == "METFI Autonomous Finance Controller"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.PORT == 8000
