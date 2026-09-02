"""
Unit tests for the AuditRepository persistence layer and database model conversions.
"""

import pytest

from app.audit.models import AuditEventDB
from app.audit.repository import InMemoryAuditRepository
from app.domain.audit import (
    Actor,
    ActorType,
    AIModelTrace,
    AuditEvent,
    AuditEventType,
)


@pytest.mark.asyncio
async def test_in_memory_audit_repository_crud_lifecycle() -> None:
    repo = InMemoryAuditRepository()

    e1 = AuditEvent(
        event_id="evt_repo_01",
        event_type=AuditEventType.CASE_CREATED,
        case_id="case_repo_101",
        correlation_id="corr_repo_101",
        sequence_number=1,
        source_component="pipeline",
        actor=Actor(actor_type=ActorType.SYSTEM, actor_id="pipeline_v1"),
        payload={"order_id": "ORD-1"},
        previous_event_hash="GENESIS",
        event_hash="hash_repo_01",
    )
    e2 = AuditEvent(
        event_id="evt_repo_02",
        event_type=AuditEventType.RECONCILIATION_COMPLETED,
        case_id="case_repo_101",
        correlation_id="corr_repo_101",
        sequence_number=2,
        source_component="reconciliation_engine",
        actor=Actor(actor_type=ActorType.DETERMINISTIC_ENGINE, actor_id="rules"),
        payload={"classification": "EXACT_MATCH"},
        previous_event_hash="hash_repo_01",
        event_hash="hash_repo_02",
    )

    # Append
    await repo.append_event(e1)
    await repo.append_event(e2)

    # Get by ID
    res1 = await repo.get_event_by_id("evt_repo_01")
    assert res1 is not None
    assert res1.event_id == "evt_repo_01"

    # Get by Case ID
    case_events = await repo.get_events_by_case_id("case_repo_101")
    assert len(case_events) == 2
    assert case_events[0].sequence_number == 1
    assert case_events[1].sequence_number == 2

    # Get Latest Event
    latest = await repo.get_latest_event_for_case("case_repo_101")
    assert latest is not None
    assert latest.event_id == "evt_repo_02"

    # Duplicate Event ID Rejection
    with pytest.raises(ValueError, match="already exists"):
        await repo.append_event(e1)


def test_audit_event_db_model_roundtrip() -> None:
    domain_event = AuditEvent(
        event_id="evt_roundtrip_01",
        event_type=AuditEventType.INVESTIGATION_COMPLETED,
        case_id="case_roundtrip_101",
        correlation_id="corr_roundtrip_101",
        sequence_number=1,
        source_component="investigation_service",
        actor=Actor(actor_type=ActorType.AI_INVESTIGATOR, actor_id="gemini-1.5-pro"),
        payload={"recommendation": "AUTO_RECONCILE"},
        ai_trace=AIModelTrace(
            provider="gemini",
            model_name="gemini-1.5-pro",
            latency_ms=98.5,
            verification_status="VERIFIED",
        ),
        previous_event_hash="GENESIS",
        event_hash="hash_rt_01",
    )

    # Convert to DB model
    db_model = AuditEventDB.from_domain(domain_event)
    assert db_model.event_id == "evt_roundtrip_01"
    assert db_model.actor_type == "AI_INVESTIGATOR"

    # Convert back to Domain model
    restored = db_model.to_domain()
    assert restored.event_id == domain_event.event_id
    assert restored.event_type == domain_event.event_type
    assert restored.ai_trace is not None
    assert restored.ai_trace.provider == "gemini"
    assert restored.ai_trace.latency_ms == 98.5
