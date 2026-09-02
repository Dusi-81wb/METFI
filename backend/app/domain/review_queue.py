"""
Domain models for the Human Finance Review and Escalation Queue.

Provides structured queue models for cases requiring human controller review or escalation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.action import ActionType
from app.domain.investigation import EvidenceReference, VerifierStatus
from app.domain.policy import PolicyDecision


class ReviewPriority(StrEnum):
    """Operational priority for items in the human review queue."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewStatus(StrEnum):
    """Lifecycle status of a human review queue item."""

    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class ReviewItem(BaseModel):
    """
    Structured item in the controller review queue.
    """

    model_config = ConfigDict(frozen=True)

    review_id: str = Field(
        default_factory=lambda: f"rev_{uuid4().hex[:12]}",
        description="Unique review queue identifier",
    )
    case_id: str = Field(description="Associated reconciliation case ID")
    priority: ReviewPriority = Field(
        default=ReviewPriority.MEDIUM,
        description="Assigned review urgency level",
    )
    status: ReviewStatus = Field(
        default=ReviewStatus.PENDING,
        description="Current queue status",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Specific reasons why the case was routed to review",
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Certified evidence field references attached to this case",
    )
    investigation_summary: str | None = Field(
        default=None,
        description="AI investigation explanation summary if available",
    )
    verifier_status: VerifierStatus | None = Field(
        default=None,
        description="AI Verifier decision if available",
    )
    policy_decision: PolicyDecision | None = Field(
        default=None,
        description="Policy engine decision that routed the case to review",
    )
    assigned_to: str | None = Field(
        default=None,
        description="Identifier of the human finance controller reviewing the case",
    )
    resolution_action: ActionType | None = Field(
        default=None,
        description="Action selected by human reviewer upon resolution",
    )
    resolution_notes: str | None = Field(
        default=None,
        description="Human controller notes explaining resolution rationale",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of queue entry",
    )
    resolved_at: str | None = Field(
        default=None,
        description="UTC ISO 8601 timestamp of review completion",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional case context and metadata",
    )

    def claim(self, user_id: str) -> ReviewItem:
        """Assign review item to a controller."""
        data = self.model_dump()
        data.update(
            {
                "status": ReviewStatus.IN_REVIEW,
                "assigned_to": user_id,
            }
        )
        return ReviewItem.model_validate(data)

    def resolve(self, action: ActionType, notes: str) -> ReviewItem:
        """Mark review item as resolved with an action and audit notes."""
        data = self.model_dump()
        data.update(
            {
                "status": ReviewStatus.RESOLVED,
                "resolution_action": action,
                "resolution_notes": notes,
                "resolved_at": datetime.now(UTC).isoformat(),
            }
        )
        return ReviewItem.model_validate(data)

    def escalate(
        self, notes: str, new_priority: ReviewPriority = ReviewPriority.HIGH
    ) -> ReviewItem:
        """Escalate review item to senior finance management."""
        data = self.model_dump()
        data.update(
            {
                "status": ReviewStatus.ESCALATED,
                "priority": new_priority,
                "resolution_notes": notes,
            }
        )
        return ReviewItem.model_validate(data)
