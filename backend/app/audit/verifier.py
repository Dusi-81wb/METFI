"""
Audit Integrity Verifier.

Independently checks hash-chain continuity, sequence monotonicity, payload integrity,
and lifecycle transition coherence.

Strict Non-Negotiable Rules:
1. Returns VALID or INTEGRITY_FAILURE. Never silently repairs or ignores corruption.
2. Every integrity check must produce detailed diagnostic violation messages.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.audit.hasher import AuditHasher
from app.domain.audit import AuditEvent, AuditEventType


class AuditIntegrityStatus(StrEnum):
    """Integrity verification verdict."""

    VALID = "VALID"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


class AuditIntegrityResult(BaseModel):
    """
    Structured outcome of an independent audit trail verification check.
    """

    model_config = ConfigDict(frozen=True)

    status: AuditIntegrityStatus = Field(description="Overall verification verdict")
    case_id: str = Field(description="Audited reconciliation case ID")
    events_verified_count: int = Field(description="Total number of events verified in the chain")
    is_hash_chain_valid: bool = Field(
        description="True if all event hashes and previous hash links match cryptographically"
    )
    is_sequence_monotonic: bool = Field(
        description="True if sequence numbers strictly increment 1, 2, 3... with no gaps"
    )
    is_lifecycle_coherent: bool = Field(
        description="True if event sequence adheres to the financial state machine"
    )
    violations: list[str] = Field(
        default_factory=list,
        description="Detailed diagnostic explanations of any integrity violations detected",
    )
    verified_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC timestamp when verification executed",
    )


class AuditIntegrityVerifier:
    """
    Independent audit verification engine validating tamper evidence and state coherence.
    """

    @classmethod
    def verify_case_timeline(cls, case_id: str, events: list[AuditEvent]) -> AuditIntegrityResult:
        """
        Perform cryptographic and logical integrity verification on a case event timeline.
        """
        if not events:
            return AuditIntegrityResult(
                status=AuditIntegrityStatus.VALID,
                case_id=case_id,
                events_verified_count=0,
                is_hash_chain_valid=True,
                is_sequence_monotonic=True,
                is_lifecycle_coherent=True,
                violations=[],
            )

        violations: list[str] = []
        is_hash_chain_valid = True
        is_seq_monotonic = True
        is_lifecycle_coherent = True

        seen_event_ids: set[str] = set()
        has_authorized_action = False

        # Sort by sequence number for validation
        sorted_events = sorted(events, key=lambda e: e.sequence_number)

        for i, ev in enumerate(sorted_events):
            # Check 1: Duplicate Event ID
            if ev.event_id in seen_event_ids:
                violations.append(f"Duplicate event ID '{ev.event_id}' found in case '{case_id}'.")
                is_seq_monotonic = False
            seen_event_ids.add(ev.event_id)

            # Check 2: Monotonic sequence numbers (1-indexed, step=1)
            expected_seq = i + 1
            if ev.sequence_number != expected_seq:
                violations.append(
                    f"Sequence break at index {i}: "
                    f"Expected sequence_number {expected_seq}, observed {ev.sequence_number}."
                )
                is_seq_monotonic = False

            # Check 3: Genesis previous_event_hash on first event
            if i == 0:
                if ev.previous_event_hash != "GENESIS":
                    violations.append(
                        f"First event '{ev.event_id}' has invalid previous_event_hash "
                        f"'{ev.previous_event_hash}', expected 'GENESIS'."
                    )
                    is_hash_chain_valid = False
            else:
                prev_ev = sorted_events[i - 1]
                if ev.previous_event_hash != prev_ev.event_hash:
                    violations.append(
                        f"Broken hash link between event {prev_ev.event_id} "
                        f"(hash: {prev_ev.event_hash}) and event {ev.event_id} "
                        f"(previous_hash: {ev.previous_event_hash})."
                    )
                    is_hash_chain_valid = False

            # Check 4: Payload Hash Verification
            if not AuditHasher.verify_event_hash(ev):
                violations.append(
                    f"Tampered or corrupted payload in event '{ev.event_id}'. "
                    "Stored hash does not match computed hash."
                )
                is_hash_chain_valid = False

            # Check 5: Lifecycle Coherence
            if ev.event_type == AuditEventType.ACTION_AUTHORIZED:
                has_authorized_action = True
            elif ev.event_type in (AuditEventType.ACTION_EXECUTING, AuditEventType.ACTION_EXECUTED):
                if not has_authorized_action:
                    violations.append(
                        f"Lifecycle violation: Action event '{ev.event_type.value}' "
                        "occurred without prior ACTION_AUTHORIZED."
                    )
                    is_lifecycle_coherent = False

        overall_status = (
            AuditIntegrityStatus.VALID if not violations else AuditIntegrityStatus.INTEGRITY_FAILURE
        )

        return AuditIntegrityResult(
            status=overall_status,
            case_id=case_id,
            events_verified_count=len(events),
            is_hash_chain_valid=is_hash_chain_valid,
            is_sequence_monotonic=is_seq_monotonic,
            is_lifecycle_coherent=is_lifecycle_coherent,
            violations=violations,
        )
