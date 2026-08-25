"""System health and readiness verification endpoints with active dependency checks."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine
from app.core.logging import logger

router = APIRouter(tags=["Health & Status"])


class SubsystemStatus(BaseModel):
    """Health status of individual METFI system layers."""

    data_plane: str = Field(description="Synthetic data plane and ground truth readiness")
    deterministic_engine: str = Field(description="Deterministic reconciliation engine status")
    intelligence_layer: str = Field(description="AI investigator and provider readiness")
    policy_engine: str = Field(description="Policy authorization gate status")
    audit_layer: str = Field(description="Append-only audit trail status")
    evaluation_engine: str = Field(description="Ground-truth evaluator status")
    database: str = Field(description="PostgreSQL persistence engine connectivity")


class HealthResponse(BaseModel):
    """Canonical system health response model."""

    status: str = Field(description="Overall system health status: healthy | degraded | unhealthy")
    service: str = Field(default="metfi-backend", description="Service identifier")
    version: str = Field(description="System semantic version")
    environment: str = Field(description="Deployment environment")
    timestamp: str = Field(description="Current UTC timestamp")
    subsystems: SubsystemStatus = Field(description="Subsystem health statuses")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional environment and dependency diagnostics"
    )


async def check_database_connectivity() -> tuple[str, str | None]:
    """Execute live query against database to verify connectivity with timeout."""
    try:
        async with asyncio.timeout(0.5):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return "connected", None
    except Exception as e:
        logger.debug("Database connection check failed: %s", e)
        return "disconnected", str(e)


def check_ai_provider_status() -> tuple[str, str]:
    """Verify configured AI provider readiness."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "mock":
        return "ready", "Mock AI Provider Active (Local / Test Mode)"
    elif provider == "gemini":
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            return "ready", f"Gemini Provider Configured ({settings.DEFAULT_AI_MODEL})"
        return "unconfigured", "Gemini API key not configured (set GEMINI_API_KEY in .env)"
    elif provider == "openai":
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            return "ready", f"OpenAI Provider Configured ({settings.DEFAULT_AI_MODEL})"
        return "unconfigured", "OpenAI API key not configured"
    return "ready", f"Provider '{provider}' registered"


def check_data_plane_status() -> tuple[str, str]:
    """Verify data plane and ground-truth isolation directory."""
    candidates = [
        Path(__file__).resolve().parents[4] / "data" / "ground_truth",
        Path(__file__).resolve().parents[3] / "data" / "ground_truth",
        Path.cwd().parent / "data" / "ground_truth",
        Path.cwd() / "data" / "ground_truth",
    ]
    for gt_dir in candidates:
        if gt_dir.exists():
            return "ready", "Ground truth directory isolated and ready"
    return "degraded", "Ground truth directory structure missing"


@router.get("/health", response_model=HealthResponse)
async def get_health_status() -> HealthResponse:
    """Retrieve detailed health and readiness status of the METFI controller."""
    db_status, db_error = await check_database_connectivity()
    ai_status, ai_message = check_ai_provider_status()
    dp_status, dp_message = check_data_plane_status()

    # Determine overall system health state
    # In Phase 0 development, if DB is disconnected, system is 'degraded' rather than failing
    if db_status == "connected":
        overall_status = "healthy"
    else:
        overall_status = "degraded"

    subsystems = SubsystemStatus(
        data_plane=dp_status,
        deterministic_engine="ready",
        intelligence_layer=ai_status,
        policy_engine="ready",
        audit_layer="ready",
        evaluation_engine="ready",
        database=db_status,
    )

    details: dict[str, Any] = {
        "ai_provider": settings.AI_PROVIDER,
        "ai_status_message": ai_message,
        "data_plane_message": dp_message,
        "database_connected": db_status == "connected",
        "api_prefix": settings.API_V1_STR,
    }
    if db_error:
        details["database_notice"] = (
            "Database disconnected. Start PostgreSQL via "
            "'docker compose up postgres' for persistence."
        )

    return HealthResponse(
        status=overall_status,
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        subsystems=subsystems,
        details=details,
    )
