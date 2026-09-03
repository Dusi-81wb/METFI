"""
Integration tests for Track 04 AI Finance Controller API endpoints:
- GET /api/v1/controller/summary
- POST /api/v1/controller/run-loop
- POST /api/v1/controller/qa
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_controller_summary_endpoint() -> None:
    """GET /api/v1/controller/summary returns books, cash position, and match rate."""
    response = client.get("/api/v1/controller/summary?dataset_id=dev_500")
    assert response.status_code == 200
    data = response.json()

    assert data["batch_id"] == "dev_500"
    assert data["total_cases"] == 500
    assert data["match_rate_pct"] == 60.0
    assert "cash_position" in data
    assert "books_status" in data
    assert "honest_exception_list" in data
    assert len(data["honest_exception_list"]) == 200


def test_run_finance_ops_loop_endpoint() -> None:
    """POST /api/v1/controller/run-loop executes on 50+ records and returns report."""
    response = client.post(
        "/api/v1/controller/run-loop",
        json={"dataset_id": "dev_500", "max_records": 60},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["batch_id"] == "dev_500"
    assert data["records_evaluated"] > 50
    assert data["throughput_records_per_sec"] > 0
    assert data["books_status"]["is_balanced"] is True


def test_settlement_qa_endpoint() -> None:
    """POST /api/v1/controller/qa handles controller queries."""
    response = client.post(
        "/api/v1/controller/qa",
        json={"question": "What is our current cash position?", "dataset_id": "dev_500"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "Bank Settled Cash" in data["answer"]
    assert data["confidence"] > 0.9
