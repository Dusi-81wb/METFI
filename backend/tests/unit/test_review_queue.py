"""
Unit tests for the Human Controller Review Queue and Escalation Workflows.
"""

import pytest

from app.domain.action import ActionType
from app.domain.audit import AuditEventType
from app.domain.review_queue import ReviewPriority, ReviewStatus
from app.services.review_queue_service import ReviewQueueService


@pytest.mark.asyncio
async def test_review_queue_enqueue_and_list() -> None:
    service = ReviewQueueService()

    # Enqueue two items
    item1, event1 = await service.enqueue_case(
        case_id="case_rq_01",
        reasons=["Amount mismatch under unknown fee policy"],
        priority=ReviewPriority.HIGH,
    )
    assert item1.case_id == "case_rq_01"
    assert item1.status == ReviewStatus.PENDING
    assert item1.priority == ReviewPriority.HIGH
    assert event1.event_type == AuditEventType.REVIEW_ENQUEUED

    item2, _ = await service.enqueue_case(
        case_id="case_rq_02",
        reasons=["Currency conversion discrepancy"],
        priority=ReviewPriority.CRITICAL,
    )

    # List items
    items = await service.list_items()
    assert len(items) == 2
    # Critical should be first
    assert items[0].review_id == item2.review_id


@pytest.mark.asyncio
async def test_review_queue_claim_resolve_escalate() -> None:
    service = ReviewQueueService()
    item, _ = await service.enqueue_case(
        case_id="case_rq_03",
        reasons=["Manual verification required"],
        priority=ReviewPriority.MEDIUM,
    )

    # Claim
    claimed = await service.claim_item(review_id=item.review_id, user_id="user_finance_ops")
    assert claimed.status == ReviewStatus.IN_REVIEW
    assert claimed.assigned_to == "user_finance_ops"

    # Resolve
    resolved, res_event = await service.resolve_item(
        review_id=item.review_id,
        resolution_action=ActionType.AUTO_RECONCILE,
        notes="Bank batch slip confirmed manual match.",
    )
    assert resolved.status == ReviewStatus.RESOLVED
    assert resolved.resolution_action == ActionType.AUTO_RECONCILE
    assert res_event.event_type == AuditEventType.REVIEW_RESOLVED


@pytest.mark.asyncio
async def test_review_queue_escalate() -> None:
    service = ReviewQueueService()
    item, _ = await service.enqueue_case(
        case_id="case_rq_04",
        reasons=["Suspected fraudulent duplicate submission"],
        priority=ReviewPriority.HIGH,
    )

    escalated, esc_event = await service.escalate_item(
        review_id=item.review_id,
        notes="Escalating to Compliance and Risk team.",
        new_priority=ReviewPriority.CRITICAL,
    )
    assert escalated.status == ReviewStatus.ESCALATED
    assert escalated.priority == ReviewPriority.CRITICAL
    assert esc_event.event_type == AuditEventType.REVIEW_ESCALATED
