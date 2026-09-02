"""
Unit tests for the PolicyEvaluator metric calculation harness.
"""

from decimal import Decimal

import pytest

from app.domain.action import ActionType
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.investigation import (
    BoundedRecommendation,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecisionOutcome,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.evaluation.policy_evaluator import PolicyEvaluator, PolicyTestCase


@pytest.mark.asyncio
async def test_policy_evaluator_metrics_calculation() -> None:
    # 1. Exact Match case
    m1 = MonetaryEvidence(
        payment_gross=Decimal("100.00"), settled_net=Decimal("100.00"), is_fee_policy_known=True
    )
    ev1 = ReconciliationEvidence(
        monetary=m1,
        currency=CurrencyEvidence(is_currency_matched=True),
        timing=TimingEvidence(
            payment_timestamp="2026-08-30T10:00:00Z",
            settlement_timestamp="2026-08-30T12:00:00Z",
            is_within_sla_window=True,
        ),
        reference=ReferenceEvidence(),
        cardinality=CardinalityEvidence(),
    )
    rec1 = ReconciliationResult(
        case_id="case_ev_01",
        order_id="ORD-EV-01",
        classification=ExceptionType.EXACT_MATCH,
        policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        evidence=ev1,
        reason_code="RULE_EXACT_MATCH",
        summary="Exact match",
        reconciled_at="2026-08-30T12:00:00Z",
    )
    inv1 = InvestigationResult(
        case_id="case_ev_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Exact Match",
        evidence_references=[],
        recommended_action=BoundedRecommendation.AUTO_RECONCILE,
    )
    ver1 = VerificationResult(
        investigation_id=inv1.investigation_id,
        case_id="case_ev_01",
        verifier_status=VerifierStatus.VERIFIED,
        is_evidence_supported=True,
        are_references_valid=True,
        is_deterministic_truth_preserved=True,
        is_recommendation_safe=True,
        verifier_notes="Verified",
    )
    env1 = VerifiedInvestigationEnvelope(
        case_id="case_ev_01",
        deterministic_result=rec1,
        investigation=inv1,
        verification=ver1,
        final_canonical_status=ExceptionType.EXACT_MATCH,
        final_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        summary="Exact Match Summary",
    )
    tc1 = PolicyTestCase(
        case_id="case_ev_01",
        scenario_name="Exact Match",
        deterministic_result=rec1,
        envelope=env1,
        policy_config=DomainPolicyConfig(
            fee_tax_policy=FeeTaxPolicy(fee_rate=Decimal("0.02"), tax_rate_on_fee=Decimal("0.18"))
        ),
        requested_action=ActionType.AUTO_RECONCILE,
        expected_decision=PolicyDecisionOutcome.ALLOW,
        expected_autonomous_authorized=True,
        should_test_duplicate=True,
    )

    evaluator = PolicyEvaluator()
    metrics, reports = await evaluator.evaluate_scenarios([tc1])

    assert metrics.total_cases_evaluated == 1
    assert metrics.policy_correctness_rate == 1.0
    assert metrics.duplicate_prevention_rate == 1.0
    assert metrics.deterministic_truth_preservation_rate == 1.0
    assert metrics.simulated_execution_success_rate == 1.0
    assert len(reports) == 1
