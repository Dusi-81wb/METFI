"""
Integration tests for FastAPI AI Investigation endpoints (/api/v1/investigation).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_investigation_run_endpoint_success() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. First trigger reconciliation on dev_500 to ensure dataset exists on disk
        rec_resp = await client.post(
            "/api/v1/reconciliation/run",
            json={"dataset_id": "dev_500"},
        )
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        target_case = rec_data["results"][0]["case_id"]

        # 2. Call investigation endpoint
        inv_resp = await client.post(
            "/api/v1/investigation/run",
            json={
                "case_id": target_case,
                "dataset_id": "dev_500",
                "provider_override": "mock",
            },
        )
        assert inv_resp.status_code == 200
        inv_data = inv_resp.json()

        assert inv_data["case_id"] == target_case
        assert "deterministic_result" in inv_data
        assert "investigation" in inv_data
        assert "verification" in inv_data
        assert "final_canonical_status" in inv_data
        assert "final_policy_outcome" in inv_data


@pytest.mark.asyncio
async def test_investigation_run_nonexistent_case() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/api/v1/investigation/run",
            json={
                "case_id": "nonexistent_case_12345",
                "dataset_id": "dev_500",
            },
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]
