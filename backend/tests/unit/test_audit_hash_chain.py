"""
Unit tests for canonical JSON serialization and cryptographic hash chaining.
"""

from app.audit.hasher import AuditHasher
from app.domain.audit import (
    Actor,
    ActorType,
    AuditEvent,
    AuditEventType,
)


def test_canonical_serialization_is_deterministic() -> None:
    d1 = {"b": 2, "a": 1, "nested": {"z": 26, "y": 25}}
    d2 = {"nested": {"y": 25, "z": 26}, "a": 1, "b": 2}

    s1 = AuditHasher.canonical_serialize(d1)
    s2 = AuditHasher.canonical_serialize(d2)

    assert s1 == s2
    assert s1 == '{"a":1,"b":2,"nested":{"y":25,"z":26}}'


def test_compute_event_hash_consistency() -> None:
    raw_payload = {
        "event_id": "evt_tst_01",
        "event_type": "CASE_CREATED",
        "case_id": "case_101",
        "correlation_id": "corr_101",
        "sequence_number": 1,
        "payload": {"amount": "100.00"},
    }
    h1 = AuditHasher.compute_event_hash(raw_payload, previous_event_hash="GENESIS")
    h2 = AuditHasher.compute_event_hash(raw_payload, previous_event_hash="GENESIS")
    h3 = AuditHasher.compute_event_hash(raw_payload, previous_event_hash="DIFF_PREV_HASH")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex string


def test_verify_event_hash() -> None:
    event_dict = {
        "event_id": "evt_tst_02",
        "event_type": AuditEventType.RECONCILIATION_COMPLETED,
        "case_id": "case_102",
        "correlation_id": "corr_102",
        "sequence_number": 1,
        "source_component": "reconciliation_engine",
        "actor": Actor(actor_type=ActorType.DETERMINISTIC_ENGINE, actor_id="rule_matcher"),
        "payload": {"classification": "EXACT_MATCH"},
        "previous_event_hash": "GENESIS",
    }
    event = AuditEvent.model_validate(event_dict)
    computed_hash = AuditHasher.compute_event_hash(
        event.model_dump(mode="json"), previous_event_hash="GENESIS"
    )

    # Valid event with matching hash
    valid_event = event.model_copy(update={"event_hash": computed_hash})
    assert AuditHasher.verify_event_hash(valid_event) is True

    # Tampered event with wrong hash
    tampered_event = event.model_copy(update={"event_hash": "malicious_fake_hash_1234567890"})
    assert AuditHasher.verify_event_hash(tampered_event) is False
