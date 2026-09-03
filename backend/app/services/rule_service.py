"""
Rule Service for Microsoft Purview-style Rule Studio.
Manages user-defined and system-default classification & policy gating rules.
"""

from __future__ import annotations

import re
import threading
from decimal import Decimal
from typing import Any

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import ReconciliationEvidence
from app.schemas.rules import (
    CreateRuleRequest,
    CustomRule,
    RuleCondition,
    RuleField,
    RuleOperator,
    RuleType,
)


class RuleService:
    """
    Thread-safe repository and evaluator for custom reconciliation governance rules.
    """

    _instance: RuleService | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._rules: dict[str, CustomRule] = {}
        self._init_system_rules()

    @classmethod
    def get_instance(cls) -> RuleService:
        """Singleton accessor for RuleService."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _init_system_rules(self) -> None:
        """Seed default system classification and policy gating rules."""
        system_rules = [
            CustomRule(
                rule_id="SYS_RULE_ZERO_TOLERANCE",
                name="Strict Exact Balance Check",
                description="Verifies gross volume matches settled net + fee deductions exactly.",
                rule_type=RuleType.CLASSIFICATION,
                condition=RuleCondition(
                    field=RuleField.SETTLEMENT_AMOUNT_DELTA,
                    operator=RuleOperator.EQ,
                    value=0.0,
                ),
                target_classification=ExceptionType.EXACT_MATCH,
                target_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
                priority=100,
                is_enabled=True,
                is_system=True,
            ),
            CustomRule(
                rule_id="SYS_RULE_CONTRACT_FEE_CAP",
                name="Contractual Interchange Cap (₹25.00)",
                description=(
                    "Quarantines cases where gateway fee exceeds contractual threshold >₹25.00."
                ),
                rule_type=RuleType.CLASSIFICATION,
                condition=RuleCondition(
                    field=RuleField.FEE_VARIANCE,
                    operator=RuleOperator.GT,
                    value=25.0,
                ),
                target_classification=ExceptionType.FEE_DISCREPANCY,
                target_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
                priority=80,
                is_enabled=True,
                is_system=True,
            ),
            CustomRule(
                rule_id="SYS_RULE_SLA_WINDOW",
                name="Settlement SLA 72h Cut-off Window",
                description=(
                    "Flags timing discrepancies when bank settlement exceeds standard 72h window."
                ),
                rule_type=RuleType.CLASSIFICATION,
                condition=RuleCondition(
                    field=RuleField.HOURS_TO_SETTLEMENT,
                    operator=RuleOperator.GT,
                    value=72.0,
                ),
                target_classification=ExceptionType.DATE_MISMATCH,
                target_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
                priority=70,
                is_enabled=True,
                is_system=True,
            ),
        ]
        for r in system_rules:
            self._rules[r.rule_id] = r

    def list_rules(
        self,
        rule_type: RuleType | None = None,
        is_enabled: bool | None = None,
    ) -> list[CustomRule]:
        """List all rules sorted by priority (lowest integer = highest priority)."""
        rules = list(self._rules.values())
        if rule_type is not None:
            rules = [r for r in rules if r.rule_type == rule_type]
        if is_enabled is not None:
            rules = [r for r in rules if r.is_enabled == is_enabled]
        return sorted(rules, key=lambda x: (x.priority, x.name))

    def get_rule(self, rule_id: str) -> CustomRule | None:
        """Retrieve a specific rule by ID."""
        return self._rules.get(rule_id)

    def create_rule(self, req: CreateRuleRequest) -> CustomRule:
        """Create and register a new user-defined custom rule."""
        clean_name = re.sub(r"[^A-Za-z0-9]+", "_", req.name.upper()).strip("_")
        rule_id = f"RULE_USER_{clean_name}_{len(self._rules) + 1}"
        rule = CustomRule(
            rule_id=rule_id,
            name=req.name,
            description=req.description,
            rule_type=req.rule_type,
            condition=req.condition,
            target_classification=req.target_classification,
            target_policy_outcome=req.target_policy_outcome,
            priority=req.priority,
            is_enabled=req.is_enabled,
            is_system=False,
        )
        self._rules[rule_id] = rule
        return rule

    def toggle_rule(self, rule_id: str, is_enabled: bool) -> CustomRule | None:
        """Enable or disable an existing rule."""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        updated = rule.model_copy(update={"is_enabled": is_enabled})
        self._rules[rule_id] = updated
        return updated

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a custom rule (system rules cannot be deleted)."""
        rule = self._rules.get(rule_id)
        if not rule or rule.is_system:
            return False
        del self._rules[rule_id]
        return True

    def reset_to_defaults(self) -> None:
        """Reset rule repository to initial system defaults."""
        self._rules.clear()
        self._init_system_rules()

    def evaluate_custom_classification(
        self, evidence: ReconciliationEvidence
    ) -> tuple[CustomRule, ExceptionType, str] | None:
        """
        Evaluate enabled custom classification rules against evidence.

        Returns:
            (matched_rule, target_classification, reason_code) or None if no rule matches.
        """
        active_rules = [
            r
            for r in self.list_rules(rule_type=RuleType.CLASSIFICATION, is_enabled=True)
            if not r.is_system  # User rules evaluated first
        ]
        for rule in active_rules:
            if self._matches_condition(rule.condition, evidence):
                reason = f"CUSTOM_RULE_{rule.rule_id}"
                return rule, rule.target_classification, reason
        return None

    def _extract_field_value(self, field: RuleField, evidence: ReconciliationEvidence) -> Any:
        """Extract typed value from evidence based on RuleField."""
        if field == RuleField.FEE_VARIANCE:
            return float(abs(evidence.monetary.fee_variance))
        elif field == RuleField.TAX_VARIANCE:
            return float(abs(evidence.monetary.tax_variance))
        elif field == RuleField.SETTLEMENT_AMOUNT_DELTA:
            return float(abs(evidence.monetary.settlement_amount_delta))
        elif field == RuleField.PAYMENT_GROSS:
            return float(evidence.monetary.payment_gross or Decimal("0.00"))
        elif field == RuleField.SETTLED_NET:
            return float(evidence.monetary.settled_net or Decimal("0.00"))
        elif field == RuleField.HOURS_TO_SETTLEMENT:
            return float(evidence.timing.hours_to_settlement or 0.0)
        elif field == RuleField.CURRENCY:
            return evidence.currency.payment_currency
        elif field == RuleField.CARDINALITY_SETTLEMENT_COUNT:
            return evidence.cardinality.settlement_count
        return None

    def _matches_condition(
        self, condition: RuleCondition, evidence: ReconciliationEvidence
    ) -> bool:
        """Evaluate whether evidence satisfies a RuleCondition."""
        val = self._extract_field_value(condition.field, evidence)
        if val is None:
            return False

        # Primary condition evaluation
        if not self._compare(val, condition.operator, condition.value):
            return False

        # Secondary condition evaluation (if configured)
        sec_field = condition.secondary_field
        sec_op = condition.secondary_operator
        sec_val_target = condition.secondary_value
        if sec_field and sec_op and sec_val_target is not None:
            sec_val = self._extract_field_value(sec_field, evidence)
            if sec_val is None:
                return False
            if not self._compare(sec_val, sec_op, sec_val_target):
                return False

        return True

    def _compare(self, actual: Any, op: RuleOperator, benchmark: Any) -> bool:
        """Compare actual value against benchmark value using RuleOperator."""
        try:
            if isinstance(actual, (int, float)) and isinstance(benchmark, (int, float, str)):
                b_val = float(benchmark)
                if op == RuleOperator.LTE:
                    return actual <= b_val
                elif op == RuleOperator.GTE:
                    return actual >= b_val
                elif op == RuleOperator.LT:
                    return actual < b_val
                elif op == RuleOperator.GT:
                    return actual > b_val
                elif op == RuleOperator.EQ:
                    return abs(actual - b_val) < 0.001
                elif op == RuleOperator.NEQ:
                    return abs(actual - b_val) >= 0.001

            # String comparison
            s_actual = str(actual).upper().strip()
            s_bench = str(benchmark).upper().strip()
            if op == RuleOperator.EQ:
                return s_actual == s_bench
            elif op == RuleOperator.NEQ:
                return s_actual != s_bench
        except (ValueError, TypeError):
            return False

        return False
