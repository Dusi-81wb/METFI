"""
Domain models for Deterministic Corporate Policy Rules and Authorization Decisions.

Strict Non-Negotiable Rules:
1. Deterministic policy rules govern all operational authorizations.
2. AI recommendations are inputs to policy evaluation, not authorization authorities.
3. Unknown or unconfigured policies must fail closed (REVIEW_REQUIRED / UNRESOLVED).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType
from app.domain.fee_policy import FeeTaxPolicy


class PolicyDecisionOutcome(StrEnum):
    """Deterministic policy authorization decision outcomes."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REVIEW = "REVIEW"
    UNRESOLVED = "UNRESOLVED"


class VarianceTolerancePolicy(BaseModel):
    """
    Configurable tolerance thresholds for automatic reconciliation of fee/tax variances.
    """

    model_config = ConfigDict(frozen=True)

    max_absolute_fee_variance: Decimal = Field(
        default=Decimal("1.00"),
        description="Maximum absolute fee discrepancy tolerated for auto-reconciliation",
    )
    max_absolute_tax_variance: Decimal = Field(
        default=Decimal("0.50"),
        description="Maximum absolute tax discrepancy tolerated for auto-reconciliation",
    )
    max_percentage_variance: Decimal = Field(
        default=Decimal("0.02"),
        description="Maximum percentage discrepancy (e.g. 0.02 = 2%) tolerated",
    )
    allow_rounding_delta: bool = Field(
        default=True,
        description="True to allow rounding discrepancies of <= 0.02 under standard rounding rules",
    )


class RetryPolicy(BaseModel):
    """
    Policy governing automated retry requests for transient or missing settlements.
    """

    model_config = ConfigDict(frozen=True)

    max_retry_attempts: int = Field(
        default=3,
        description="Maximum number of retry attempts permitted per case",
    )
    retryable_exceptions: list[ExceptionType] = Field(
        default_factory=lambda: [
            ExceptionType.MISSING_SETTLEMENT,
            ExceptionType.DATE_MISMATCH,
        ],
        description="List of exception types eligible for automated retry requests",
    )
    cooldown_seconds: int = Field(
        default=300,
        description="Mandatory cooldown between consecutive retry requests in seconds",
    )


class DomainPolicyConfig(BaseModel):
    """
    Complete corporate domain policy bundle evaluated by the Deterministic Policy Engine.
    """

    model_config = ConfigDict(frozen=True)

    policy_version: str = Field(default="1.0.0", description="Semantic policy ruleset version")
    fee_tax_policy: FeeTaxPolicy | None = Field(
        default=None, description="Contractual fee and GST tax matrix"
    )
    variance_tolerance: VarianceTolerancePolicy = Field(
        default_factory=VarianceTolerancePolicy,
        description="Configured monetary variance tolerances",
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Configured retry policy limits",
    )
    auto_reconciliation_enabled: bool = Field(
        default=True,
        description="Global master switch for autonomous reconciliation",
    )
    max_auto_reconcile_amount: Decimal = Field(
        default=Decimal("100000.00"),
        description="Maximum transaction amount permitted for autonomous resolution",
    )


class PolicyDecision(BaseModel):
    """
    Deterministic authorization decision output by the Policy Engine.
    """

    model_config = ConfigDict(frozen=True)

    decision: PolicyDecisionOutcome = Field(
        description="Core authorization verdict (ALLOW, DENY, REVIEW, UNRESOLVED)"
    )
    is_autonomous_authorized: bool = Field(
        description="True if an autonomous controlled action may execute without manual review"
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Explicit policy rule codes triggered during evaluation",
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Specific safety violations preventing authorization",
    )
    applicable_rules: list[str] = Field(
        default_factory=list,
        description="Identifiers of all policy rules evaluated against the case",
    )
    policy_version: str = Field(default="1.0.0", description="Evaluated policy version")
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of policy evaluation",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Audit and diagnostic metadata"
    )
