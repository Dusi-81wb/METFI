"""Integration tests for end-to-end reconciliation service and FastAPI endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.reconciliation_service import ReconciliationService


@pytest.mark.asyncio
async def test_reconciliation_service_dev_500() -> None:
    service = ReconciliationService()
    batch_result = service.reconcile_from_disk("dev_500")

    assert batch_result.total_cases == 500
    assert batch_result.class_distribution["EXACT_MATCH"] == 300
    assert batch_result.policy_distribution["AUTO_RECONCILE"] == 300
    assert batch_result.performance_metrics.throughput_records_per_sec > 10000.0


@pytest.mark.asyncio
async def test_api_reconciliation_run_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/reconciliation/run", json={"dataset_id": "dev_500"})
        assert response.status_code == 200
        data = response.json()
        assert data["total_cases"] == 500
        assert data["class_distribution"]["EXACT_MATCH"] == 300
        assert "performance_metrics" in data


@pytest.mark.asyncio
async def test_api_benchmark_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/reconciliation/benchmark", json={"dataset_id": "dev_500"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 500
        assert data["overall_accuracy"] == 1.0
        assert data["macro_f1"] == 1.0
        assert data["false_match_rate"] == 0.0
