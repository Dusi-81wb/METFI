"""Integration and smoke tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Verify that the root endpoint returns 200 OK and service metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "operational"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient) -> None:
    """Verify that /api/v1/health returns health status and subsystem details."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["version"] == "0.1.0"
    assert "subsystems" in data
    assert data["subsystems"]["deterministic_engine"] == "ready"
    assert data["subsystems"]["policy_engine"] == "ready"
    assert data["subsystems"]["audit_layer"] == "ready"
    assert data["subsystems"]["data_plane"] == "ready"
    assert data["subsystems"]["evaluation_engine"] == "ready"
    assert "database" in data["subsystems"]
    assert "details" in data


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_root_health_endpoint(async_client: AsyncClient) -> None:
    """Verify that /health returns 200 and canonical health payload."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "subsystems" in data
