"""
Pydantic API schemas for Audit Trail, Verification, and Observability endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.audit.verifier import AuditIntegrityStatus
from app.domain.audit import AuditEvent


class CaseAuditTrailResponse(BaseModel):
    """Response payload containing full chronological audit timeline for a case."""

    case_id: str = Field(description="Associated reconciliation case identifier")
    event_count: int = Field(description="Total number of audit events in the case timeline")
    events: list[AuditEvent] = Field(
        description="Chronological ordered sequence of immutable audit events"
    )


class CaseIntegrityVerificationResponse(BaseModel):
    """Response payload containing cryptographic and lifecycle integrity verification result."""

    case_id: str = Field(description="Audited reconciliation case ID")
    status: AuditIntegrityStatus = Field(
        description="Overall verification verdict (VALID / INTEGRITY_FAILURE)"
    )
    events_verified_count: int = Field(description="Total events verified in the chain")
    is_hash_chain_valid: bool = Field(
        description="True if all event hashes and previous hash links match"
    )
    is_sequence_monotonic: bool = Field(
        description="True if sequence numbers are strictly contiguous"
    )
    is_lifecycle_coherent: bool = Field(
        description="True if state transitions match lifecycle rules"
    )
    violations: list[str] = Field(
        default_factory=list, description="Diagnostic list of any violations detected"
    )
    verified_at: str = Field(description="UTC timestamp when verification occurred")


class AuditMetricsResponse(BaseModel):
    """Response payload containing operational observability metrics and latencies."""

    counters: dict[str, int] = Field(description="Operational event and error counters")
    errors: dict[str, int] = Field(description="Error counts categorized by anomaly type")
    latencies: dict[str, Any] = Field(
        description="Stage-level latency statistics (avg, p95, min, max)"
    )
