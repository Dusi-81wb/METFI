"""
SQLAlchemy ORM models for PostgreSQL audit persistence.

Strict Non-Negotiable Rules:
1. Audit tables are strictly append-only.
2. Comprehensive indexes support case timeline reconstruction and correlation lookups.
"""

from __future__ import annotations

import json

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.audit import Actor, ActorType, AIModelTrace, AuditEvent, AuditEventType
from app.domain.investigation import EvidenceReference


class AuditEventDB(Base):
    """
    SQLAlchemy model representing an append-only audit event in PostgreSQL.
    """

    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_component: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    evidence_references_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reconciliation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    investigation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_decision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    review_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_audit_events_case_seq", "case_id", "sequence_number", unique=True),
        Index("ix_audit_events_correlation_seq", "correlation_id", "sequence_number"),
    )

    def to_domain(self) -> AuditEvent:
        """Convert database record to immutable domain model."""
        payload = json.loads(self.payload_json) if self.payload_json else {}
        evidence_raw = (
            json.loads(self.evidence_references_json) if self.evidence_references_json else []
        )
        evidence_refs = [EvidenceReference.model_validate(er) for er in evidence_raw]

        ai_trace = None
        if self.ai_trace_json:
            ai_trace = AIModelTrace.model_validate_json(self.ai_trace_json)

        return AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType(self.event_type),
            case_id=self.case_id,
            correlation_id=self.correlation_id,
            sequence_number=self.sequence_number,
            timestamp=self.timestamp,
            source_component=self.source_component,
            actor=Actor(
                actor_type=ActorType(self.actor_type),
                actor_id=self.actor_id,
                display_name=self.display_name,
            ),
            event_version=self.event_version,
            payload=payload,
            evidence_references=evidence_refs,
            policy_version=self.policy_version,
            ai_trace=ai_trace,
            reconciliation_id=self.reconciliation_id,
            investigation_id=self.investigation_id,
            verification_id=self.verification_id,
            policy_decision_id=self.policy_decision_id,
            action_id=self.action_id,
            review_id=self.review_id,
            previous_event_hash=self.previous_event_hash,
            event_hash=self.event_hash,
        )

    @classmethod
    def from_domain(cls, event: AuditEvent) -> AuditEventDB:
        """Create database record from domain model."""
        ai_trace_str = event.ai_trace.model_dump_json() if event.ai_trace else None
        evidence_str = json.dumps(
            [er.model_dump() for er in event.evidence_references], sort_keys=True
        )
        payload_str = json.dumps(event.payload, sort_keys=True)

        return cls(
            event_id=event.event_id,
            event_type=event.event_type.value,
            case_id=event.case_id,
            correlation_id=event.correlation_id,
            sequence_number=event.sequence_number,
            timestamp=event.timestamp,
            source_component=event.source_component,
            actor_type=event.actor.actor_type.value,
            actor_id=event.actor.actor_id,
            display_name=event.actor.display_name,
            event_version=event.event_version,
            payload_json=payload_str,
            evidence_references_json=evidence_str,
            policy_version=event.policy_version,
            ai_trace_json=ai_trace_str,
            reconciliation_id=event.reconciliation_id,
            investigation_id=event.investigation_id,
            verification_id=event.verification_id,
            policy_decision_id=event.policy_decision_id,
            action_id=event.action_id,
            review_id=event.review_id,
            previous_event_hash=event.previous_event_hash,
            event_hash=event.event_hash,
        )
