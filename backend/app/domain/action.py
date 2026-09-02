"""
Domain models for Policy-Gated Resolution and Controlled Operational Actions.

Strict Non-Negotiable Rules:
1. Authority Hierarchy:
   Deterministic Truth > Deterministic Policy Engine > Verified AI Recommendation > Action Executor.
2. AI does NOT authorize actions or mutate canonical financial truth.
3. Every action has explicit state transitions, preconditions, and idempotency guarantees.
4. Actions must be immutable after creation except through validated state transitions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.investigation import EvidenceReference


class ActionType(StrEnum):
    """Controlled operational action types authorized by the Policy Engine."""

    AUTO_RECONCILE = "AUTO_RECONCILE"
    MARK_FOR_REVIEW = "MARK_FOR_REVIEW"
    ESCALATE = "ESCALATE"
    REQUEST_RETRY = "REQUEST_RETRY"
    REQUEST_MANUAL_VERIFICATION = "REQUEST_MANUAL_VERIFICATION"


class ActionState(StrEnum):
    """Explicit lifecycle states for a Controlled Action."""

    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AuthorizationStatus(StrEnum):
    """Authorization status determined by the Deterministic Policy Engine."""

    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    PENDING_REVIEW = "PENDING_REVIEW"


class InvalidStateTransitionError(ValueError):
    """Raised when attempting an unauthorized or illegal state machine transition."""


class UnauthorizedExecutionError(RuntimeError):
    """Raised when attempting to execute an action without valid policy authorization."""


class ActionPreconditions(BaseModel):
    """
    Explicit checklist of verifiable preconditions required to authorize an action.
    """

    model_config = ConfigDict(frozen=True)

    is_deterministic_truth_preserved: bool = Field(
        default=True,
        description="True if requested action does not contradict deterministic financial truth",
    )
    is_verifier_passed: bool = Field(
        default=True,
        description="True if AI investigation was verified without rejection",
    )
    is_evidence_complete: bool = Field(
        default=True,
        description="True if all required evidence references are present and certified",
    )
    is_within_variance_tolerance: bool = Field(
        default=True,
        description="True if monetary/tax variances are within configured policy tolerances",
    )
    is_within_retry_limit: bool = Field(
        default=True,
        description="True if retry count does not exceed policy thresholds",
    )
    is_policy_known: bool = Field(
        default=True,
        description="True if the applicable domain policy is explicitly configured",
    )
    has_valid_idempotency_key: bool = Field(
        default=True,
        description="True if a valid unique idempotency key is supplied",
    )

    def is_all_satisfied(self) -> bool:
        """Return True if all individual preconditions are met."""
        return (
            self.is_deterministic_truth_preserved
            and self.is_verifier_passed
            and self.is_evidence_complete
            and self.is_within_variance_tolerance
            and self.is_within_retry_limit
            and self.is_policy_known
            and self.has_valid_idempotency_key
        )


class ActionResult(BaseModel):
    """Structured result produced by the Action Executor following execution."""

    model_config = ConfigDict(frozen=True)

    action_id: str = Field(description="Associated controlled action ID")
    case_id: str = Field(description="Associated reconciliation case ID")
    action_type: ActionType = Field(description="Executed action type")
    status: ActionState = Field(description="Terminal execution status (EXECUTED / FAILED)")
    side_effects_simulated: list[str] = Field(
        default_factory=list,
        description="List of simulated domain side-effects",
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Operational outcome metadata and simulated responses"
    )
    error_message: str | None = Field(
        default=None, description="Failure details if execution failed"
    )
    executed_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of execution completion",
    )
    latency_ms: float = Field(default=0.0, description="Execution duration in milliseconds")


class ControlledAction(BaseModel):
    """
    Immutable domain model representing a policy-governed controlled operational action.
    """

    model_config = ConfigDict(frozen=True)

    action_id: str = Field(
        default_factory=lambda: f"act_{uuid4().hex[:12]}",
        description="Unique action identifier",
    )
    case_id: str = Field(description="Associated reconciliation case ID")
    action_type: ActionType = Field(description="Specific controlled action type")
    state: ActionState = Field(default=ActionState.REQUESTED, description="Current lifecycle state")
    authorization_status: AuthorizationStatus = Field(
        default=AuthorizationStatus.PENDING_REVIEW,
        description="Authorization decision from policy engine",
    )
    idempotency_key: str = Field(
        description="Deterministic idempotency key preventing duplicate side-effects"
    )
    policy_version: str = Field(
        default="1.0.0", description="Version of the policy ruleset evaluated"
    )
    preconditions: ActionPreconditions = Field(
        default_factory=ActionPreconditions,
        description="Evaluated preconditions checklist",
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Field-level citations supporting this action",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters (e.g. retry endpoint, escalation target)",
    )
    requested_by: str = Field(
        default="system_policy",
        description="Origin of the action request (e.g. 'ai_investigator', 'finance_ops')",
    )
    rejection_reasons: list[str] = Field(
        default_factory=list, description="Reasons for authorization denial or rejection"
    )
    requested_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC timestamp when action was requested",
    )
    authorized_at: str | None = Field(
        default=None, description="UTC timestamp when policy authorized the action"
    )
    executed_at: str | None = Field(
        default=None, description="UTC timestamp when execution concluded"
    )
    execution_result: ActionResult | None = Field(
        default=None, description="Result payload if executed"
    )

    @classmethod
    def generate_idempotency_key(
        cls,
        case_id: str,
        action_type: ActionType,
        payload: dict[str, Any] | None = None,
        policy_version: str = "1.0.0",
    ) -> str:
        """
        Deterministically compute a cryptographic SHA-256 idempotency key.
        """
        payload_str = json.dumps(payload or {}, sort_keys=True)
        raw_key = f"{case_id}:{action_type.value}:{payload_str}:{policy_version}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]

    def transition_to(
        self,
        new_state: ActionState,
        authorization_status: AuthorizationStatus | None = None,
        rejection_reasons: list[str] | None = None,
        execution_result: ActionResult | None = None,
    ) -> ControlledAction:
        """
        Safely transition action state following the strict state machine.

        Allowed transitions:
        REQUESTED -> VALIDATING | REJECTED
        VALIDATING -> AUTHORIZED | REJECTED
        AUTHORIZED -> EXECUTING | FAILED
        EXECUTING -> EXECUTED | FAILED
        """
        valid_transitions: dict[ActionState, set[ActionState]] = {
            ActionState.REQUESTED: {ActionState.VALIDATING, ActionState.REJECTED},
            ActionState.VALIDATING: {ActionState.AUTHORIZED, ActionState.REJECTED},
            ActionState.AUTHORIZED: {
                ActionState.EXECUTING,
                ActionState.FAILED,
                ActionState.REJECTED,
            },
            ActionState.EXECUTING: {ActionState.EXECUTED, ActionState.FAILED},
            ActionState.EXECUTED: set(),
            ActionState.REJECTED: set(),
            ActionState.FAILED: set(),
        }

        allowed = valid_transitions.get(self.state, set())
        if new_state not in allowed:
            msg = f"Illegal transition from {self.state} to {new_state} for {self.action_id}."
            raise InvalidStateTransitionError(msg)

        now_iso = datetime.now(UTC).isoformat()
        auth_status = authorization_status or self.authorization_status
        auth_at = self.authorized_at
        exec_at = self.executed_at

        if new_state == ActionState.AUTHORIZED:
            auth_status = AuthorizationStatus.AUTHORIZED
            auth_at = now_iso
        elif new_state == ActionState.REJECTED:
            auth_status = AuthorizationStatus.DENIED
        elif new_state in (ActionState.EXECUTED, ActionState.FAILED):
            exec_at = now_iso

        reasons = list(self.rejection_reasons)
        if rejection_reasons:
            reasons.extend(rejection_reasons)

        data = self.model_dump()
        data.update(
            {
                "state": new_state,
                "authorization_status": auth_status,
                "authorized_at": auth_at,
                "executed_at": exec_at,
                "rejection_reasons": reasons,
                "execution_result": execution_result or self.execution_result,
            }
        )
        return ControlledAction.model_validate(data)
