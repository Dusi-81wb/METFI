"""
Audit Service.

Coordinates sanitization, cryptographic hash-chaining, append-only persistence,
and case timeline integrity verification.
"""

from __future__ import annotations

from typing import Any

from app.audit.hasher import AuditHasher
from app.audit.repository import AuditRepository, InMemoryAuditRepository
from app.audit.sanitizer import AuditSanitizer
from app.audit.verifier import AuditIntegrityResult, AuditIntegrityVerifier
from app.domain.audit import (
    Actor,
    ActorType,
    AIModelTrace,
    AuditEvent,
    AuditEventType,
)
from app.domain.investigation import EvidenceReference


class AuditService:
    """
    Central service managing the append-only, tamper-evident audit ledger.
    """

    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository or InMemoryAuditRepository()

    async def record_event(
        self,
        event_type: AuditEventType,
        case_id: str,
        correlation_id: str,
        source_component: str,
        actor: Actor | None = None,
        payload: dict[str, Any] | None = None,
        evidence_references: list[EvidenceReference] | None = None,
        policy_version: str | None = None,
        ai_trace: AIModelTrace | None = None,
        reconciliation_id: str | None = None,
        investigation_id: str | None = None,
        verification_id: str | None = None,
        policy_decision_id: str | None = None,
        action_id: str | None = None,
        review_id: str | None = None,
    ) -> AuditEvent:
        """
        Record a sanitized, cryptographically chained audit event append-only.
        """
        # 1. Sanitize payload and redact secrets
        clean_payload = AuditSanitizer.sanitize_payload(payload or {})

        # 2. Determine sequence number and previous event hash
        latest_event = await self.repository.get_latest_event_for_case(case_id)
        if latest_event is None:
            seq_num = 1
            prev_hash = "GENESIS"
        else:
            seq_num = latest_event.sequence_number + 1
            prev_hash = latest_event.event_hash

        actor_obj = actor or Actor(actor_type=ActorType.SYSTEM, actor_id="system")

        # 3. Create initial event instance
        initial_event = AuditEvent(
            event_type=event_type,
            case_id=case_id,
            correlation_id=correlation_id,
            sequence_number=seq_num,
            source_component=source_component,
            actor=actor_obj,
            payload=clean_payload,
            evidence_references=evidence_references or [],
            policy_version=policy_version,
            ai_trace=ai_trace,
            reconciliation_id=reconciliation_id,
            investigation_id=investigation_id,
            verification_id=verification_id,
            policy_decision_id=policy_decision_id,
            action_id=action_id,
            review_id=review_id,
            previous_event_hash=prev_hash,
            event_hash="",  # Placeholder before hashing
        )

        # 4. Compute cryptographic event hash
        event_dict = initial_event.model_dump(mode="json")
        computed_hash = AuditHasher.compute_event_hash(
            event_dict=event_dict,
            previous_event_hash=prev_hash,
        )

        final_data = initial_event.model_dump()
        final_data["event_hash"] = computed_hash
        final_event = AuditEvent.model_validate(final_data)

        # 5. Persist append-only
        return await self.repository.append_event(final_event)

    async def get_case_audit_trail(self, case_id: str) -> list[AuditEvent]:
        """Retrieve full ordered chronological audit trail for a case."""
        return await self.repository.get_events_by_case_id(case_id)

    async def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        """Retrieve single audit event by ID."""
        return await self.repository.get_event_by_id(event_id)

    async def get_correlation_audit_trail(self, correlation_id: str) -> list[AuditEvent]:
        """Retrieve all audit events under a correlation ID."""
        return await self.repository.get_events_by_correlation_id(correlation_id)

    async def verify_case_integrity(self, case_id: str) -> AuditIntegrityResult:
        """Run independent cryptographic and lifecycle integrity verification on a case."""
        events = await self.repository.get_events_by_case_id(case_id)
        return AuditIntegrityVerifier.verify_case_timeline(case_id=case_id, events=events)
