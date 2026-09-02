"""
API Router for Corporate Policy Evaluation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.policy import (
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
)
from app.services.policy_service import PolicyService

policy_router = APIRouter(prefix="/policy", tags=["Policy Engine"])


def get_policy_service() -> PolicyService:
    """Dependency injection factory for PolicyService."""
    return PolicyService()


@policy_router.post("/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_policy_endpoint(
    req: PolicyEvaluationRequest,
    service: PolicyService = Depends(get_policy_service),
) -> PolicyEvaluationResponse:
    """
    Evaluate deterministic policy rules on a reconciliation case without executing actions.
    """
    decision, preconditions = service.evaluate_case_policy(
        case_id=req.case_id,
        deterministic_result=req.deterministic_result,
        envelope=req.envelope,
        policy_config=req.policy_config,
        requested_action=req.requested_action,
        retry_count=req.retry_count,
    )

    return PolicyEvaluationResponse(
        case_id=req.case_id,
        decision=decision,
        preconditions=preconditions,
    )
