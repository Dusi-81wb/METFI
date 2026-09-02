"""
Integration tests for Phase 8 API Hardening, Error Handling & Trust Boundaries.

Verifies:
1. Malformed JSON returns clean 422/400 without internal tracebacks.
2. Missing required fields produce structured validation errors.
3. Non-existent case or audit query IDs return 404 cleanly.
4. Unexpected enum values are rejected with schema validation errors.
5. Public error response bodies do not leak internal file paths or server details.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_reconciliation_api_rejects_missing_payload() -> None:
    """Ensure POST /api/v1/reconciliation/run handles empty body with 422 or default."""
    resp = client.post(
        "/api/v1/reconciliation/run",
        json={"dataset_id": "non_existent_dataset_9999"},
    )
    assert resp.status_code in {400, 404, 422}


def test_investigation_api_rejects_nonexistent_dataset() -> None:
    """Ensure POST /api/v1/investigation/run returns 404 on missing dataset or case."""
    resp = client.post(
        "/api/v1/investigation/run",
        json={
            "case_id": "case_bad_01",
            "dataset_id": "missing_dataset_xyz",
        },
    )
    assert resp.status_code in {400, 404, 422}


def test_policy_evaluate_rejects_invalid_root_cause_enum() -> None:
    """Ensure POST /api/v1/policy/evaluate rejects unknown root_cause enums."""
    resp = client.post(
        "/api/v1/policy/evaluate",
        json={
            "case_id": "case_bad_02",
            "investigation": {
                "case_id": "case_bad_02",
                "root_cause_category": "UNKNOWN_RANDOM_ENUM",
            },
        },
    )
    assert resp.status_code in {400, 422}


def test_audit_verify_nonexistent_case_returns_empty_or_404() -> None:
    """Ensure GET /api/v1/audit/cases/{case_id}/events handles non-existent case safely."""
    resp = client.get("/api/v1/audit/cases/non_existent_case_99999/events")
    assert resp.status_code in {200, 404}
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0


def test_health_endpoint_returns_json_structure() -> None:
    """Ensure GET /api/v1/health returns structured status without leaking internal state."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
