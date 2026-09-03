"""
Unit tests for Microsoft Purview-style RuleService.
Validates rule creation, prioritization, toggling, deletion, and condition evaluation.
"""

from decimal import Decimal

import pytest

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.schemas.rules import (
    CreateRuleRequest,
    RuleCondition,
    RuleField,
    RuleOperator,
    RuleType,
)
from app.services.rule_service import RuleService


@pytest.fixture(autouse=True)
def reset_rules():
    """Reset rules to system defaults before each test."""
    service = RuleService.get_instance()
    service.reset_to_defaults()
    yield
    service.reset_to_defaults()


def _build_test_evidence(
    fee_variance: Decimal = Decimal("30.00"),
    currency: str = "INR",
    hours_to_settlement: float = 12.0,
) -> ReconciliationEvidence:
    return ReconciliationEvidence(
        monetary=MonetaryEvidence(
            payment_gross=Decimal("1000.00"),
            settled_net=Decimal("970.00"),
            standard_contract_fee=Decimal("20.00"),
            fee_deducted=Decimal("50.00"),
            fee_variance=fee_variance,
            is_fee_policy_known=True,
            is_fee_compliant=False,
        ),
        currency=CurrencyEvidence(
            payment_currency=currency,
            settlement_currency=currency,
            ledger_currency=currency,
            is_currency_matched=True,
        ),
        timing=TimingEvidence(
            hours_to_settlement=hours_to_settlement,
            is_within_sla_window=True,
        ),
        reference=ReferenceEvidence(
            is_order_id_matched=True,
            is_payment_id_matched=True,
        ),
        cardinality=CardinalityEvidence(
            settlement_count=1,
            has_duplicate_settlement=False,
            has_missing_settlement=False,
        ),
    )


def test_rule_service_initializes_system_rules():
    """Verify standard default system rules are present and protected."""
    service = RuleService.get_instance()
    rules = service.list_rules()
    assert len(rules) >= 3
    system_rules = [r for r in rules if r.is_system]
    assert len(system_rules) >= 3
    assert any(r.rule_id == "SYS_RULE_ZERO_TOLERANCE" for r in system_rules)


def test_rule_service_create_and_list_custom_rule():
    """Verify creating a custom classification rule adds it to the catalog."""
    service = RuleService.get_instance()
    req = CreateRuleRequest(
        name="Micro-Fee Tolerance Waiver",
        description="Auto-reconciles gateway fee variances within ₹35.00 limit.",
        rule_type=RuleType.CLASSIFICATION,
        condition=RuleCondition(
            field=RuleField.FEE_VARIANCE,
            operator=RuleOperator.LTE,
            value=35.0,
        ),
        target_classification=ExceptionType.EXACT_MATCH,
        target_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        priority=10,
    )
    created = service.create_rule(req)
    assert created.name == "Micro-Fee Tolerance Waiver"
    assert created.is_system is False
    assert created.priority == 10

    all_rules = service.list_rules()
    assert any(r.rule_id == created.rule_id for r in all_rules)


def test_rule_service_toggle_and_delete():
    """Verify toggling active status and deleting user custom rules."""
    service = RuleService.get_instance()
    req = CreateRuleRequest(
        name="Temporary Holiday Rule",
        description="Testing toggle and delete mechanics.",
        condition=RuleCondition(
            field=RuleField.HOURS_TO_SETTLEMENT,
            operator=RuleOperator.LTE,
            value=96.0,
        ),
    )
    rule = service.create_rule(req)

    # 1. Toggle disabled
    toggled = service.toggle_rule(rule.rule_id, is_enabled=False)
    assert toggled is not None
    assert toggled.is_enabled is False

    # 2. Verify filter by is_enabled
    active_only = service.list_rules(is_enabled=True)
    assert not any(r.rule_id == rule.rule_id for r in active_only)

    # 3. System rule protection
    sys_del = service.delete_rule("SYS_RULE_ZERO_TOLERANCE")
    assert sys_del is False  # Cannot delete system rule

    # 4. Custom rule deletion
    usr_del = service.delete_rule(rule.rule_id)
    assert usr_del is True
    assert service.get_rule(rule.rule_id) is None


def test_rule_service_evaluates_evidence_matching():
    """Verify evidence evaluation successfully triggers custom rule outcome."""
    service = RuleService.get_instance()
    # Create rule: Fee variance <= 35.00 should be classified as EXACT_MATCH
    service.create_rule(
        CreateRuleRequest(
            name="Tier-1 Fee Auto Waiver",
            description="Fee delta up to 35.00 classified as clean match.",
            condition=RuleCondition(
                field=RuleField.FEE_VARIANCE,
                operator=RuleOperator.LTE,
                value=35.0,
            ),
            target_classification=ExceptionType.EXACT_MATCH,
            priority=5,
        )
    )

    ev_matching = _build_test_evidence(fee_variance=Decimal("30.00"))
    match_result = service.evaluate_custom_classification(ev_matching)
    assert match_result is not None
    rule, target_cls, reason = match_result
    assert target_cls == ExceptionType.EXACT_MATCH
    assert "CUSTOM_RULE" in reason

    ev_exceeding = _build_test_evidence(fee_variance=Decimal("55.00"))
    no_match = service.evaluate_custom_classification(ev_exceeding)
    assert no_match is None


def test_rule_service_secondary_condition():
    """Verify multi-condition rules (e.g. Fee <= 40 AND Currency == INR)."""
    service = RuleService.get_instance()
    service.create_rule(
        CreateRuleRequest(
            name="INR-Only Fee Exception Waiver",
            description="Waives minor fee variance only for domestic INR transactions.",
            condition=RuleCondition(
                field=RuleField.FEE_VARIANCE,
                operator=RuleOperator.LTE,
                value=40.0,
                secondary_field=RuleField.CURRENCY,
                secondary_operator=RuleOperator.EQ,
                secondary_value="INR",
            ),
            target_classification=ExceptionType.EXACT_MATCH,
            priority=5,
        )
    )

    # INR currency matches
    ev_inr = _build_test_evidence(fee_variance=Decimal("35.00"), currency="INR")
    assert service.evaluate_custom_classification(ev_inr) is not None

    # USD currency does not match secondary condition
    ev_usd = _build_test_evidence(fee_variance=Decimal("35.00"), currency="USD")
    assert service.evaluate_custom_classification(ev_usd) is None
