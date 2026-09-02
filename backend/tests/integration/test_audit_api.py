"""
Integration tests for Audit Trail, Case Verification, and Observability Metrics FastAPI routes.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.audit import get_audit_service
from app.audit.service import AuditService
from app.domain.audit import (
    Actor,
    ActorType,
    AuditEventType,
)
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_audit_api_case_timeline_and_verification() -> None:
    audit_service: AuditService = get_audit_service()
    case_id = "case_api_audit_01"
    corr_id = "corr_api_audit_01"

    # Seed events with valid lifecycle
    e1 = await audit_service.record_event(
        event_type=AuditEventType.CASE_CREATED,
        case_id=case_id,
        correlation_id=corr_id,
        source_component="pipeline",
        actor=Actor(actor_type=ActorType.SYSTEM, actor_id="pipeline_v1"),
        payload={"order_id": "ORD-API-01"},
    )
    await audit_service.record_event(
        event_type=AuditEventType.ACTION_AUTHORIZED,
        case_id=case_id,
        correlation_id=corr_id,
        source_component="policy_engine",
        actor=Actor(actor_type=ActorType.POLICY_ENGINE, actor_id="policy_engine_v1"),
        action_id="act_api_01",
        payload={"action_type": "AUTO_RECONCILE"},
    )
    await audit_service.record_event(
        event_type=AuditEventType.ACTION_EXECUTED,
        case_id=case_id,
        correlation_id=corr_id,
        source_component="executor",
        actor=Actor(actor_type=ActorType.ACTION_EXECUTOR, actor_id="executor_v1"),
        action_id="act_api_01",
        payload={"status": "EXECUTED"},
    )

    # 1. GET /api/v1/audit/cases/{case_id}
    resp_timeline = client.get(f"/api/v1/audit/cases/{case_id}")
    assert resp_timeline.status_code == 200
    timeline_data = resp_timeline.json()
    assert timeline_data["case_id"] == case_id
    assert timeline_data["event_count"] >= 2
    assert len(timeline_data["events"]) >= 2

    # 2. GET /api/v1/audit/cases/{case_id}/verify
    resp_verify = client.get(f"/api/v1/audit/cases/{case_id}/verify")
    assert resp_verify.status_code == 200
    verify_data = resp_verify.json()
    assert verify_data["case_id"] == case_id
    assert verify_data["status"] == "VALID"
    assert verify_data["is_hash_chain_valid"] is True

    # 3. GET /api/v1/audit/events/{event_id}
    resp_event = client.get(f"/api/v1/audit/events/{e1.event_id}")
    assert resp_event.status_code == 200
    event_data = resp_event.json()
    assert event_data["event_id"] == e1.event_id
    assert event_data["event_type"] == "CASE_CREATED"

    # 4. GET /api/v1/audit/events/{non_existent} -> 404
    resp_404 = client.get("/api/v1/audit/events/evt_non_existent_999")
    assert resp_404.status_code == 404

    # 5. GET /api/v1/audit/metrics
    resp_metrics = client.get("/api/v1/audit/metrics")
    assert resp_metrics.status_code == 200
    metrics_data = resp_metrics.json()
    assert "counters" in metrics_data
    assert "latencies" in metrics_data
