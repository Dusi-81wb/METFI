"""
Unit tests for AuditEvent domain models, Actor models, AIModelTrace, and AuditEventType taxonomy.
"""

import pytest
from pydantic import ValidationError

from app.domain.audit import (
    Actor,
    ActorType,
    AIModelTrace,
    AuditEvent,
    AuditEventType,
)


def test_audit_event_creation_and_fields() -> None:
    event = AuditEvent(
        event_type=AuditEventType.CASE_CREATED,
        case_id="case_tst_101",
        correlation_id="corr_tst_101",
        sequence_number=1,
        source_component="test_suite",
        actor=Actor(actor_type=ActorType.SYSTEM, actor_id="unit_tester"),
        payload={"sample_key": "sample_val"},
    )
    assert event.event_id.startswith("evt_")
    assert event.event_type == AuditEventType.CASE_CREATED
    assert event.case_id == "case_tst_101"
    assert event.correlation_id == "corr_tst_101"
    assert event.sequence_number == 1
    assert event.actor.actor_type == ActorType.SYSTEM
    assert event.previous_event_hash == "GENESIS"


def test_audit_event_immutability() -> None:
    event = AuditEvent(
        event_type=AuditEventType.ACTION_AUTHORIZED,
        case_id="case_tst_102",
        correlation_id="corr_tst_102",
        sequence_number=1,
        actor=Actor(actor_type=ActorType.POLICY_ENGINE, actor_id="policy_v1"),
    )
    # Attempting to modify frozen Pydantic model must raise ValidationError
    with pytest.raises(ValidationError):
        event.case_id = "modified_case_id"  # type: ignore[misc]


def test_actor_models() -> None:
    human_actor = Actor(
        actor_type=ActorType.HUMAN_REVIEWER,
        actor_id="user_fin_controller_01",
        display_name="Senior Controller",
    )
    assert human_actor.actor_type == ActorType.HUMAN_REVIEWER
    assert human_actor.display_name == "Senior Controller"

    ai_actor = Actor(
        actor_type=ActorType.AI_INVESTIGATOR,
        actor_id="gemini-1.5-pro",
    )
    assert ai_actor.actor_type == ActorType.AI_INVESTIGATOR


def test_ai_model_trace_model() -> None:
    trace = AIModelTrace(
        provider="gemini",
        model_name="gemini-1.5-pro",
        prompt_version="1.2.0",
        latency_ms=145.2,
        verification_status="VERIFIED",
    )
    assert trace.provider == "gemini"
    assert trace.latency_ms == 145.2
    assert trace.verification_status == "VERIFIED"
