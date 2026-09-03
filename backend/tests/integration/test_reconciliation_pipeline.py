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
        assert data["overall_accuracy"] >= 0.95
        assert data["false_match_rate"] == 0.0


@pytest.mark.asyncio
async def test_api_case_detail_endpoint() -> None:
    """Verify GET /api/v1/reconciliation/cases/{case_id} returns live facts and agent analysis."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test case_demo_101
        resp = await client.get("/api/v1/reconciliation/cases/case_demo_101")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "case_23b2926ab448" or "case" in data["case_id"]
        assert data["classification"] == "FEE_DISCREPANCY"
        assert data["facts"]["financial_variance"] == 50.0
        assert data["facts"]["ledger_expected_amount"] == 10000.0
        assert data["ai_verifier"]["status"] == "VERIFIED"
        assert data["action"]["idempotency_key"] != ""
        assert len(data["payment_records"]) >= 1
        assert len(data["ledger_records"]) >= 1

        # Test case_demo_103 (missing settlement)
        resp_103 = await client.get("/api/v1/reconciliation/cases/case_demo_103")
        assert resp_103.status_code == 200
        data_103 = resp_103.json()
        assert data_103["classification"] == "MISSING_SETTLEMENT"
        assert data_103["facts"]["financial_variance"] == 18200.0
        assert data_103["facts"]["gross_payment_amount"] == 18200.0
        assert len(data_103["settlement_records"]) == 0


@pytest.mark.asyncio
async def test_api_honest_exceptions_endpoint() -> None:
    """Verify GET /api/v1/reconciliation/exceptions returns real isolated exceptions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/reconciliation/exceptions?dataset_id=dev_500&limit=25")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) > 0
        for item in items:
            assert item["classification"] != "EXACT_MATCH"
            assert "case_id" in item
            assert "order_id" in item
            assert "variance" in item
            assert "reason" in item
