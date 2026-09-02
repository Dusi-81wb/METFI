"""
Pydantic API request and response schemas for Policy Evaluation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.action import ActionPreconditions, ActionType
from app.domain.investigation import VerifiedInvestigationEnvelope
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecision,
)
from app.domain.reconciliation_result import ReconciliationResult


class PolicyEvaluationRequest(BaseModel):
    """Request payload to evaluate corporate policy on a reconciliation result."""

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
        default=None, description="Proposed action type to evaluate"
    )
    retry_count: int = Field(default=0, description="Current retry attempt count")


class PolicyEvaluationResponse(BaseModel):
    """Response payload containing policy authorization decision."""

    case_id: str = Field(description="Reconciliation case ID")
    decision: PolicyDecision = Field(description="Evaluated policy decision")
    preconditions: ActionPreconditions = Field(description="Preconditions checklist evaluation")
