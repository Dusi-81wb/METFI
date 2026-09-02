"""
Pydantic API schemas for Action Authorization, Execution, and Review Queue.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domain.action import ActionResult, ActionType, ControlledAction
from app.domain.audit import AuditEvent
from app.domain.investigation import VerifiedInvestigationEnvelope
from app.domain.policy import DomainPolicyConfig, PolicyDecision
from app.domain.reconciliation_result import ReconciliationResult
from app.domain.review_queue import ReviewPriority


class ActionAuthorizeRequest(BaseModel):
    """Request payload to evaluate policy and issue an authorized ControlledAction."""

    case_id: str = Field(description="Unique reconciliation case ID")
    deterministic_result: ReconciliationResult = Field(
        description="Authoritative deterministic reconciliation result"
    )
    envelope: VerifiedInvestigationEnvelope | None = Field(
        default=None, description="Verified AI investigation envelope if available"
    )
    policy_config: DomainPolicyConfig | None = Field(
        default=None, description="Domain policy configuration overrides"
    )
    requested_action: ActionType | None = Field(
        default=None, description="Proposed action type to authorize"
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    requested_by: str = Field(default="api_client", description="Actor requesting the action")
    retry_count: int = Field(default=0, description="Current retry attempt count")


class ActionAuthorizeResponse(BaseModel):
    """Response payload containing generated ControlledAction and decision."""

    action: ControlledAction = Field(description="Generated ControlledAction object")
    decision: PolicyDecision = Field(description="Policy authorization decision")
    audit_events: list[AuditEvent] = Field(default_factory=list, description="Emitted audit events")


class ActionExecuteRequest(BaseModel):
    """Request payload to execute an authorized action."""

    action: ControlledAction = Field(description="Authorized ControlledAction to execute")


class ActionExecuteResponse(BaseModel):
    """Response payload containing execution outcome and side effects."""

    action: ControlledAction = Field(description="Updated ControlledAction in terminal state")
    result: ActionResult = Field(description="Structured execution outcome")
    audit_events: list[AuditEvent] = Field(default_factory=list, description="Emitted audit events")


class ReviewResolveRequest(BaseModel):
    """Payload to resolve a review item with an action and notes."""

    resolution_action: ActionType = Field(description="Selected resolution action")
    notes: str = Field(description="Human rationale notes")


class ReviewEscalateRequest(BaseModel):
    """Payload to escalate a review item."""

    notes: str = Field(description="Escalation explanation")
    new_priority: ReviewPriority = Field(
        default=ReviewPriority.HIGH, description="Escalated urgency level"
    )
