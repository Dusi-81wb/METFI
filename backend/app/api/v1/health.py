"""System health and readiness verification endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(tags=["Health & Status"])


class SubsystemStatus(BaseModel):
    """Health status of individual METFI system layers."""

    data_plane: str = Field(default="ready", description="Synthetic data plane readiness")
    deterministic_engine: str = Field(
        default="ready", description="Deterministic reconciliation engine status"
    )
    intelligence_layer: str = Field(
        default="ready", description="AI investigator and verifier layer status"
    )
    policy_engine: str = Field(default="ready", description="Policy authorization gate status")
    audit_layer: str = Field(default="ready", description="Append-only audit trail status")
    evaluation_engine: str = Field(default="ready", description="Ground-truth evaluator status")


class HealthResponse(BaseModel):
    """Canonical system health response model."""

    status: str = Field(default="healthy", description="Overall system health status")
    service: str = Field(default="metfi-backend", description="Service identifier")
    version: str = Field(description="System semantic version")
    environment: str = Field(description="Deployment environment")
    timestamp: str = Field(description="Current UTC timestamp")
    subsystems: SubsystemStatus = Field(description="Subsystem health statuses")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional environment details"
    )


@router.get("/health", response_model=HealthResponse)
async def get_health_status() -> HealthResponse:
    """Retrieve detailed health and readiness status of the METFI controller."""
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        subsystems=SubsystemStatus(),
        details={
            "ai_provider": settings.AI_PROVIDER,
            "default_model": settings.DEFAULT_AI_MODEL,
            "api_prefix": settings.API_V1_STR,
        },
    )
