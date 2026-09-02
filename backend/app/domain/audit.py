"""
Domain models for immutable audit events, actor hierarchy, and lifecycle traceability.

Strict Non-Negotiable Rules:
1. Audit Events are immutable after creation. No UPDATE or DELETE paths exist.
2. Every event contains correlation IDs, sequence numbers, actor attribution, and hash linkage.
3. Secrets and Ground Truth labels must NEVER be persisted in audit events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.investigation import EvidenceReference


class ActorType(StrEnum):
    """Classification of actors participating in the financial reconciliation lifecycle."""

    SYSTEM = "SYSTEM"
    DETERMINISTIC_ENGINE = "DETERMINISTIC_ENGINE"
    AI_INVESTIGATOR = "AI_INVESTIGATOR"
    AI_VERIFIER = "AI_VERIFIER"
    POLICY_ENGINE = "POLICY_ENGINE"
    ACTION_EXECUTOR = "ACTION_EXECUTOR"
    HUMAN_REVIEWER = "HUMAN_REVIEWER"


class Actor(BaseModel):
    """
    Attributable actor identity responsible for emitting or authorizing an audit event.
    """

    model_config = ConfigDict(frozen=True)

    actor_type: ActorType = Field(description="High-level classification of the actor")
    actor_id: str = Field(
        default="system",
        description="Identifier (e.g. 'rule_engine_v1', 'gemini-1.5-pro', 'user_finance_ops')",
    )
    display_name: str | None = Field(
        default=None, description="Human-readable actor name for UI display"
    )


class AuditEventType(StrEnum):
    """Canonical lifecycle taxonomy of financial audit trail events."""

    CASE_CREATED = "CASE_CREATED"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"
    INVESTIGATION_STARTED = "INVESTIGATION_STARTED"
    INVESTIGATION_COMPLETED = "INVESTIGATION_COMPLETED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    ACTION_REQUESTED = "ACTION_REQUESTED"
    ACTION_AUTHORIZED = "ACTION_AUTHORIZED"
    ACTION_REJECTED = "ACTION_REJECTED"
    ACTION_EXECUTING = "ACTION_EXECUTING"
    ACTION_EXECUTION_STARTED = "ACTION_EXECUTION_STARTED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_FAILED = "ACTION_FAILED"
    ACTION_EXECUTION_FAILED = "ACTION_EXECUTION_FAILED"
    REVIEW_CREATED = "REVIEW_CREATED"
    REVIEW_ENQUEUED = "REVIEW_ENQUEUED"
    REVIEW_CLAIMED = "REVIEW_CLAIMED"
    REVIEW_RESOLVED = "REVIEW_RESOLVED"
    REVIEW_ESCALATED = "REVIEW_ESCALATED"


class AIModelTrace(BaseModel):
    """
    Safe operational metadata tracking AI provider inference without leaking prompts or secrets.
    """

    model_config = ConfigDict(frozen=True)

    provider: str = Field(description="LLM Provider (e.g. 'gemini', 'openai', 'heuristic_mock')")
    model_name: str = Field(description="Specific model identifier (e.g. 'gemini-1.5-pro')")
    prompt_version: str = Field(default="1.0.0", description="Semantic version of prompt template")
    context_schema_version: str = Field(
        default="1.0.0", description="Semantic version of context builder schema"
    )
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
    verification_status: str | None = Field(
        default=None, description="Outcome of verifier check on this AI generation"
    )


class AuditEvent(BaseModel):
    """
    Immutable, correlated, and tamper-evident audit event record.
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid4().hex[:12]}",
        description="Unique immutable audit event identifier",
    )
    event_type: AuditEventType = Field(description="Classification of the lifecycle event")
    case_id: str = Field(description="Associated reconciliation case identifier")
    correlation_id: str = Field(
        default_factory=lambda: f"corr_{uuid4().hex[:12]}",
        description="Correlation identifier spanning the entire end-to-end case workflow",
    )
    sequence_number: int = Field(
        default=1,
        description="Monotonically increasing sequence number for events within this case",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of event generation",
    )
    source_component: str = Field(
        default="audit_service",
        description="Originating subsystem (e.g. 'reconciliation_engine', 'policy_engine')",
    )
    actor: Actor = Field(
        default_factory=lambda: Actor(actor_type=ActorType.SYSTEM, actor_id="system"),
        description="Attributable entity that triggered this event",
    )
    event_version: str = Field(default="1.0.0", description="Schema version of this audit event")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured event details (sanitized, redacted, and ground-truth isolated)",
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Certified evidence citations attached to this event",
    )
    policy_version: str | None = Field(
        default=None, description="Policy version evaluated if applicable"
    )
    ai_trace: AIModelTrace | None = Field(
        default=None, description="AI inference telemetry if applicable"
    )
    reconciliation_id: str | None = Field(
        default=None, description="Associated reconciliation run identifier"
    )
    investigation_id: str | None = Field(
        default=None, description="Associated AI investigation ID if applicable"
    )
    verification_id: str | None = Field(
        default=None, description="Associated AI verification ID if applicable"
    )
    policy_decision_id: str | None = Field(
        default=None, description="Associated policy decision identifier if applicable"
    )
    action_id: str | None = Field(
        default=None, description="Associated controlled action ID if applicable"
    )
    review_id: str | None = Field(
        default=None, description="Associated review queue item ID if applicable"
    )
    previous_event_hash: str = Field(
        default="GENESIS",
        description="Cryptographic SHA-256 hash of preceding event in case chain",
    )
    event_hash: str = Field(
        default="",
        description="Cryptographic SHA-256 hash computed over canonical event payload",
    )
