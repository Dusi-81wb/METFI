"""
Unit tests for the AuditIntegrityVerifier engine and adversarial tamper detection.
"""

from app.audit.hasher import AuditHasher
from app.audit.verifier import AuditIntegrityStatus, AuditIntegrityVerifier
from app.domain.audit import (
    Actor,
    ActorType,
    AuditEvent,
    AuditEventType,
)


def _build_valid_chain(case_id: str = "case_vfy_01") -> list[AuditEvent]:
    """Helper constructing a valid 3-event cryptographically linked audit chain."""
    events: list[AuditEvent] = []

    # Event 1: CASE_CREATED
    e1_dict = {
        "event_id": f"evt_{case_id}_1",
        "event_type": AuditEventType.CASE_CREATED,
        "case_id": case_id,
        "correlation_id": f"corr_{case_id}",
        "sequence_number": 1,
        "source_component": "reconciliation_pipeline",
        "actor": Actor(actor_type=ActorType.SYSTEM, actor_id="pipeline"),
        "payload": {"order_id": "ORD-1"},
        "previous_event_hash": "GENESIS",
    }
    e1 = AuditEvent.model_validate(e1_dict)
    h1 = AuditHasher.compute_event_hash(e1.model_dump(mode="json"), previous_event_hash="GENESIS")
    e1 = e1.model_copy(update={"event_hash": h1})
    events.append(e1)

    # Event 2: ACTION_AUTHORIZED
    e2_dict = {
        "event_id": f"evt_{case_id}_2",
        "event_type": AuditEventType.ACTION_AUTHORIZED,
        "case_id": case_id,
        "correlation_id": f"corr_{case_id}",
        "sequence_number": 2,
        "source_component": "policy_engine",
        "actor": Actor(actor_type=ActorType.POLICY_ENGINE, actor_id="policy_engine_v1"),
        "payload": {"action_type": "AUTO_RECONCILE"},
        "previous_event_hash": h1,
    }
    e2 = AuditEvent.model_validate(e2_dict)
    h2 = AuditHasher.compute_event_hash(e2.model_dump(mode="json"), previous_event_hash=h1)
    e2 = e2.model_copy(update={"event_hash": h2})
    events.append(e2)

    # Event 3: ACTION_EXECUTED
    e3_dict = {
        "event_id": f"evt_{case_id}_3",
        "event_type": AuditEventType.ACTION_EXECUTED,
        "case_id": case_id,
        "correlation_id": f"corr_{case_id}",
        "sequence_number": 3,
        "source_component": "action_executor",
        "actor": Actor(actor_type=ActorType.ACTION_EXECUTOR, actor_id="simulation_executor"),
        "payload": {"status": "EXECUTED"},
        "previous_event_hash": h2,
    }
    e3 = AuditEvent.model_validate(e3_dict)
    h3 = AuditHasher.compute_event_hash(e3.model_dump(mode="json"), previous_event_hash=h2)
    e3 = e3.model_copy(update={"event_hash": h3})
    events.append(e3)

    return events


def test_valid_chain_passes_verification() -> None:
    events = _build_valid_chain("case_valid_01")
    res = AuditIntegrityVerifier.verify_case_timeline("case_valid_01", events)

    assert res.status == AuditIntegrityStatus.VALID
    assert res.events_verified_count == 3
    assert res.is_hash_chain_valid is True
    assert res.is_sequence_monotonic is True
    assert res.is_lifecycle_coherent is True
    assert len(res.violations) == 0


def test_payload_tampering_detected() -> None:
    events = _build_valid_chain("case_tamper_02")
    # Adversary alters payload of Event 2 without updating hash
    tampered_payload = {"action_type": "FORGED_ACTION"}
    tampered_e2 = events[1].model_copy(update={"payload": tampered_payload})
    tampered_events = [events[0], tampered_e2, events[2]]

    res = AuditIntegrityVerifier.verify_case_timeline("case_tamper_02", tampered_events)
    assert res.status == AuditIntegrityStatus.INTEGRITY_FAILURE
    assert res.is_hash_chain_valid is False
    assert any("Tampered or corrupted payload" in v for v in res.violations)


def test_sequence_deletion_break_detected() -> None:
    events = _build_valid_chain("case_delete_02")
    # Adversary drops middle event #2 (events remain 1 and 3)
    broken_events = [events[0], events[2]]

    res = AuditIntegrityVerifier.verify_case_timeline("case_delete_02", broken_events)
    assert res.status == AuditIntegrityStatus.INTEGRITY_FAILURE
    assert res.is_sequence_monotonic is False
    assert any("Sequence break" in v for v in res.violations)


def test_lifecycle_incoherence_detected() -> None:
    events = _build_valid_chain("case_lifecycle_02")
    # Event 2 changed to RECONCILIATION_COMPLETED so ACTION_EXECUTED has no ACTION_AUTHORIZED
    e2_dict = events[1].model_dump()
    e2_dict["event_type"] = AuditEventType.RECONCILIATION_COMPLETED
    e2 = AuditEvent.model_validate(e2_dict)
    h2 = AuditHasher.compute_event_hash(
        e2.model_dump(mode="json"), previous_event_hash=events[0].event_hash
    )
    e2 = e2.model_copy(update={"event_hash": h2})

    # Update event 3 previous_hash to match new h2
    e3 = events[2].model_copy(update={"previous_event_hash": h2})
    h3 = AuditHasher.compute_event_hash(e3.model_dump(mode="json"), previous_event_hash=h2)
    e3 = e3.model_copy(update={"event_hash": h3})

    incoherent_events = [events[0], e2, e3]
    res = AuditIntegrityVerifier.verify_case_timeline("case_lifecycle_02", incoherent_events)

    assert res.status == AuditIntegrityStatus.INTEGRITY_FAILURE
    assert res.is_lifecycle_coherent is False
    assert any("Lifecycle violation" in v for v in res.violations)
