"""
Schemas for Microsoft Purview-style Custom Rule Studio.
Enables user-defined classification rules and policy gating controls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType, PolicyOutcome


class RuleField(StrEnum):
    """Field on candidate reconciliation evidence evaluated by the rule."""

    FEE_VARIANCE = "monetary.fee_variance"
    TAX_VARIANCE = "monetary.tax_variance"
    SETTLEMENT_AMOUNT_DELTA = "monetary.settlement_amount_delta"
    PAYMENT_GROSS = "monetary.payment_gross"
    SETTLED_NET = "monetary.settled_net"
    HOURS_TO_SETTLEMENT = "timing.hours_to_settlement"
    CURRENCY = "currency.payment_currency"
    CARDINALITY_SETTLEMENT_COUNT = "cardinality.settlement_count"


class RuleOperator(StrEnum):
    """Comparison operator applied to the field."""

    LTE = "<="
    GTE = ">="
    EQ = "=="
    NEQ = "!="
    LT = "<"
    GT = ">"


class RuleType(StrEnum):
    """Functional scope of the rule."""

    CLASSIFICATION = "CLASSIFICATION"
    POLICY_GATE = "POLICY_GATE"


class RuleCondition(BaseModel):
    """Atomic conditional logic evaluated against evidence."""

    model_config = ConfigDict(frozen=True)

    field: RuleField = Field(description="Evidence attribute being evaluated")
    operator: RuleOperator = Field(description="Comparison operator")
    value: float | str = Field(description="Comparison benchmark value")
    secondary_field: RuleField | None = Field(
        default=None, description="Optional secondary condition field"
    )
    secondary_operator: RuleOperator | None = Field(
        default=None, description="Optional secondary operator"
    )
    secondary_value: float | str | None = Field(
        default=None, description="Optional secondary value"
    )


class CustomRule(BaseModel):
    """
    Purview-style governance rule configuring custom classification or policy outcome.
    """

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(description="Unique rule identifier (e.g. RULE_FEE_TOLERANCE_50)")
    name: str = Field(description="Human-readable rule name")
    description: str = Field(description="Operational intent and policy justification")
    rule_type: RuleType = Field(description="Rule scope: CLASSIFICATION or POLICY_GATE")
    condition: RuleCondition = Field(description="Deterministic condition definition")
    target_classification: ExceptionType = Field(
        default=ExceptionType.FEE_DISCREPANCY,
        description="Target classification if condition matches (for CLASSIFICATION rules)",
    )
    target_policy_outcome: PolicyOutcome = Field(
        default=PolicyOutcome.REVIEW_REQUIRED,
        description="Target policy action if condition matches (for POLICY_GATE rules)",
    )
    priority: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Evaluation precedence (1 = highest priority, 100 = lowest)",
    )
    is_enabled: bool = Field(default=True, description="Whether the rule is currently active")
    is_system: bool = Field(
        default=False, description="System-default rule protected from deletion"
    )
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class CreateRuleRequest(BaseModel):
    """Request payload to create a new custom rule."""

    name: str = Field(min_length=3, max_length=100, description="Rule name")
    description: str = Field(min_length=5, max_length=300, description="Rule description")
    rule_type: RuleType = Field(default=RuleType.CLASSIFICATION)
    condition: RuleCondition
    target_classification: ExceptionType = Field(default=ExceptionType.EXACT_MATCH)
    target_policy_outcome: PolicyOutcome = Field(default=PolicyOutcome.AUTO_RECONCILE)
    priority: int = Field(default=50, ge=1, le=100)
    is_enabled: bool = Field(default=True)


class ToggleRuleRequest(BaseModel):
    """Request payload to enable or disable a rule."""

    is_enabled: bool = Field(description="New enabled status")


class RuleEvaluationResult(BaseModel):
    """Result of testing rules against evidence."""

    matched_rule: CustomRule | None
    is_rule_applied: bool
    resulting_classification: ExceptionType
    resulting_policy_outcome: PolicyOutcome
    evaluation_trace: list[str]
