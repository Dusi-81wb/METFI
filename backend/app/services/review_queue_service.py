"""
Review Queue Service.

Manages the human finance controller review queue, item claiming, resolution, and escalation.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.domain.action import ActionType
from app.domain.audit import AuditEvent, AuditEventType
from app.domain.investigation import VerifiedInvestigationEnvelope
from app.domain.policy import PolicyDecision
from app.domain.review_queue import ReviewItem, ReviewPriority, ReviewStatus


class ReviewQueueService:
    """
    In-memory and service management for controller review queue.
    """

    def __init__(self) -> None:
        self._queue: dict[str, ReviewItem] = {}
        self._case_index: dict[str, str] = {}  # case_id -> review_id
        self._lock = asyncio.Lock()

    async def enqueue_case(
        self,
        case_id: str,
        reasons: list[str],
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        envelope: VerifiedInvestigationEnvelope | None = None,
        policy_decision: PolicyDecision | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[ReviewItem, AuditEvent]:
        """
        Enqueue a case for human finance controller review.
        """
        async with self._lock:
            # Check if case is already pending in queue
            if case_id in self._case_index:
                existing_id = self._case_index[case_id]
                existing_item = self._queue[existing_id]
                if existing_item.status in (ReviewStatus.PENDING, ReviewStatus.IN_REVIEW):
                    audit_event = AuditEvent(
                        event_type=AuditEventType.REVIEW_ENQUEUED,
                        case_id=case_id,
                        payload={"review_id": existing_id, "already_enqueued": True},
                    )
                    return existing_item, audit_event

            evidence_refs = (
                envelope.investigation.evidence_references if envelope is not None else []
            )
            summary = envelope.investigation.primary_explanation if envelope is not None else None
            v_status = envelope.verification.verifier_status if envelope is not None else None

            item = ReviewItem(
                case_id=case_id,
                priority=priority,
                status=ReviewStatus.PENDING,
                reasons=reasons,
                evidence_references=evidence_refs,
                investigation_summary=summary,
                verifier_status=v_status,
                policy_decision=policy_decision,
                metadata=metadata or {},
            )

            self._queue[item.review_id] = item
            self._case_index[case_id] = item.review_id

            audit_event = AuditEvent(
                event_type=AuditEventType.REVIEW_ENQUEUED,
                case_id=case_id,
                evidence_references=evidence_refs,
                payload={
                    "review_id": item.review_id,
                    "priority": priority.value,
                    "reasons": reasons,
                },
            )

            return item, audit_event

    async def list_items(
        self,
        status: ReviewStatus | None = None,
        priority: ReviewPriority | None = None,
        limit: int = 50,
    ) -> list[ReviewItem]:
        """List queue items with optional filtering."""
        async with self._lock:
            items = list(self._queue.values())
            if status is not None:
                items = [it for it in items if it.status == status]
            if priority is not None:
                items = [it for it in items if it.priority == priority]

            # Sort by priority order and creation time
            priority_order = {
                ReviewPriority.CRITICAL: 0,
                ReviewPriority.HIGH: 1,
                ReviewPriority.MEDIUM: 2,
                ReviewPriority.LOW: 3,
            }
            items.sort(key=lambda it: (priority_order.get(it.priority, 4), it.created_at))
            return items[:limit]

    async def get_item(self, review_id: str) -> ReviewItem | None:
        """Get review item by ID."""
        async with self._lock:
            return self._queue.get(review_id)

    async def claim_item(self, review_id: str, user_id: str) -> ReviewItem:
        """Claim a review item for a controller."""
        async with self._lock:
            if review_id not in self._queue:
                raise KeyError(f"Review item {review_id} not found.")
            item = self._queue[review_id]
            updated = item.claim(user_id)
            self._queue[review_id] = updated
            return updated

    async def resolve_item(
        self, review_id: str, resolution_action: ActionType, notes: str
    ) -> tuple[ReviewItem, AuditEvent]:
        """Resolve a review item with action and rationale."""
        async with self._lock:
            if review_id not in self._queue:
                raise KeyError(f"Review item {review_id} not found.")
            item = self._queue[review_id]
            updated = item.resolve(resolution_action, notes)
            self._queue[review_id] = updated

            audit_event = AuditEvent(
                event_type=AuditEventType.REVIEW_RESOLVED,
                case_id=updated.case_id,
                payload={
                    "review_id": review_id,
                    "resolution_action": resolution_action.value,
                    "notes": notes,
                },
            )
            return updated, audit_event

    async def escalate_item(
        self, review_id: str, notes: str, new_priority: ReviewPriority = ReviewPriority.HIGH
    ) -> tuple[ReviewItem, AuditEvent]:
        """Escalate a review item."""
        async with self._lock:
            if review_id not in self._queue:
                raise KeyError(f"Review item {review_id} not found.")
            item = self._queue[review_id]
            updated = item.escalate(notes, new_priority)
            self._queue[review_id] = updated

            audit_event = AuditEvent(
                event_type=AuditEventType.REVIEW_ESCALATED,
                case_id=updated.case_id,
                payload={
                    "review_id": review_id,
                    "new_priority": new_priority.value,
                    "notes": notes,
                },
            )
            return updated, audit_event
