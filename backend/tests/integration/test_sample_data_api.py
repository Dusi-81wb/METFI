"""Integration tests for sample data explorer and randomizer API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_datasets_endpoint() -> None:
    """GET /api/v1/data/datasets returns catalog of demo datasets."""
    response = client.get("/api/v1/data/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [d["dataset_id"] for d in data]
    assert "dev_500" in ids
    assert "case_demo_101" in ids


def test_get_sample_data_endpoint() -> None:
    """GET /api/v1/data/sample returns paginated multi-source records."""
    response = client.get("/api/v1/data/sample?dataset_id=dev_500&source=all&limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == "dev_500"
    assert "payments" in payload
    assert "settlements" in payload
    assert "ledger_entries" in payload
    assert len(payload["payments"]) <= 5


def test_generate_random_transactions_endpoint() -> None:
    """POST /api/v1/data/generate-random creates synthetic records on demand."""
    payload = {
        "count": 2,
        "temperature": 0.45,
        "anomaly_profile": "FEE_DISCREPANCY",
        "seed": 888,
    }
    response = client.post("/api/v1/data/generate-random", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["seed"] == 888
    assert res["temperature"] == 0.45
    assert len(res["payments"]) == 2
    assert len(res["settlements"]) == 2
    assert "payments" in res["record_counts"]


def test_test_reconciliation_endpoint() -> None:
    """POST /api/v1/data/test-reconciliation runs deterministic reconciliation on records."""
    # First generate random records
    gen_res = client.post(
        "/api/v1/data/generate-random",
        json={"count": 1, "temperature": 0.0, "anomaly_profile": "EXACT_MATCH", "seed": 42},
    ).json()

    # Send directly to reconciliation test endpoint
    rec_response = client.post(
        "/api/v1/data/test-reconciliation",
        json={
            "dataset_id": gen_res["generated_dataset_id"],
            "payments": gen_res["payments"],
            "settlements": gen_res["settlements"],
            "ledger_entries": gen_res["ledger_entries"],
        },
    )
    assert rec_response.status_code == 200
    rec_data = rec_response.json()
    assert "results" in rec_data
    assert len(rec_data["results"]) == 1
    result = rec_data["results"][0]
    assert result["classification"] == "EXACT_MATCH"
    assert result["policy_outcome"] == "AUTO_RECONCILE"
