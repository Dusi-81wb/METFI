"""
API Router for Controlled Operational Actions and Controller Review Queue.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domain.action import UnauthorizedExecutionError
from app.domain.review_queue import ReviewItem, ReviewPriority, ReviewStatus
from app.schemas.action import (
    ActionAuthorizeRequest,
    ActionAuthorizeResponse,
    ActionExecuteRequest,
    ActionExecuteResponse,
    ReviewEscalateRequest,
    ReviewResolveRequest,
)
from app.services.policy_service import PolicyService
from app.services.review_queue_service import ReviewQueueService

actions_router = APIRouter(prefix="/actions", tags=["Controlled Actions"])

# Shared singleton instance for in-memory review queue
_review_queue_service_instance = ReviewQueueService()
_policy_service_instance = PolicyService()


def get_policy_service() -> PolicyService:
    """Dependency injection factory for PolicyService."""
    return _policy_service_instance


def get_review_queue_service() -> ReviewQueueService:
    """Dependency injection factory for ReviewQueueService."""
    return _review_queue_service_instance


@actions_router.post("/authorize", response_model=ActionAuthorizeResponse)
async def authorize_action_endpoint(
    req: ActionAuthorizeRequest,
    service: PolicyService = Depends(get_policy_service),
) -> ActionAuthorizeResponse:
    """
    Evaluate policy and generate an authorized or rejected ControlledAction.
    """
    action, decision, audit_events = await service.authorize_action(
        case_id=req.case_id,
        deterministic_result=req.deterministic_result,
        envelope=req.envelope,
        policy_config=req.policy_config,
        requested_action=req.requested_action,
        payload=req.payload,
        requested_by=req.requested_by,
        retry_count=req.retry_count,
    )

    return ActionAuthorizeResponse(
        action=action,
        decision=decision,
        audit_events=audit_events,
    )


@actions_router.post("/execute", response_model=ActionExecuteResponse)
async def execute_action_endpoint(
    req: ActionExecuteRequest,
    service: PolicyService = Depends(get_policy_service),
) -> ActionExecuteResponse:
    """
    Execute an authorized action. Rejects direct execution without valid authorization.
    """
    try:
        final_action, result, audit_events = await service.execute_action(req.action)
        return ActionExecuteResponse(
            action=final_action,
            result=result,
            audit_events=audit_events,
        )
    except UnauthorizedExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action execution forbidden: {e}",
        ) from e


@actions_router.get("/review-queue", response_model=list[ReviewItem])
async def list_review_queue_endpoint(
    status_filter: ReviewStatus | None = Query(None, alias="status"),
    priority_filter: ReviewPriority | None = Query(None, alias="priority"),
    limit: int = Query(50, ge=1, le=200),
    service: ReviewQueueService = Depends(get_review_queue_service),
) -> list[ReviewItem]:
    """
    List items currently in the controller review queue.
    """
    return await service.list_items(status=status_filter, priority=priority_filter, limit=limit)


@actions_router.post("/review-queue/{review_id}/claim", response_model=ReviewItem)
async def claim_review_endpoint(
    review_id: str,
    user_id: str = Query(..., description="User ID of controller claiming item"),
    service: ReviewQueueService = Depends(get_review_queue_service),
) -> ReviewItem:
    """
    Claim a review queue item for resolution.
    """
    try:
        return await service.claim_item(review_id=review_id, user_id=user_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {review_id} not found.",
        ) from e


@actions_router.post("/review-queue/{review_id}/resolve", response_model=ReviewItem)
async def resolve_review_endpoint(
    review_id: str,
    req: ReviewResolveRequest,
    service: ReviewQueueService = Depends(get_review_queue_service),
) -> ReviewItem:
    """
    Mark a review queue item as resolved.
    """
    try:
        item, _ = await service.resolve_item(
            review_id=review_id,
            resolution_action=req.resolution_action,
            notes=req.notes,
        )
        return item
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {review_id} not found.",
        ) from e


@actions_router.post("/review-queue/{review_id}/escalate", response_model=ReviewItem)
async def escalate_review_endpoint(
    review_id: str,
    req: ReviewEscalateRequest,
    service: ReviewQueueService = Depends(get_review_queue_service),
) -> ReviewItem:
    """
    Escalate a review queue item.
    """
    try:
        item, _ = await service.escalate_item(
            review_id=review_id,
            notes=req.notes,
            new_priority=req.new_priority,
        )
        return item
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {review_id} not found.",
        ) from e
