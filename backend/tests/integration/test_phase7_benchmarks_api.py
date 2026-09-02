"""
Integration tests for Phase 7 Benchmark Evaluation API endpoints.

Verifies:
1. GET /api/v1/benchmarks/summary returns complete 7-suite benchmark report.
2. POST /api/v1/benchmarks/run executes live evaluation and returns fresh metrics.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_get_benchmarks_summary() -> None:
    resp = client.get("/api/v1/benchmarks/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_status"] == "PASS"
    assert data["evaluation_version"] == "2.0.0"
    assert data["total_suites"] == 7
    assert len(data["suites"]) == 7

    # Verify distinct suites exist without merging
    suite_names = [s["name"] for s in data["suites"]]
    assert any("Reconciliation" in n for n in suite_names)
    assert any("Adversarial" in n for n in suite_names)
    assert any("AI" in n for n in suite_names)
    assert any("Policy" in n for n in suite_names)
    assert any("Audit" in n for n in suite_names)
    assert any("Synthetic" in n for n in suite_names)
    assert any("End-to-End" in n for n in suite_names)


def test_api_post_benchmarks_run() -> None:
    resp = client.post("/api/v1/benchmarks/run")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_status"] == "PASS"
    assert data["total_cases_evaluated"] >= 100
    for s in data["suites"]:
        assert s["passed"] is True
        assert len(s["metrics"]) >= 2
