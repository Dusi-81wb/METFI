"""
Unit tests for AI Investigator reasoning, reference validation, and fallback handling.
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
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    InvestigationStatus,
    RootCauseCategory,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.intelligence.investigator import AIInvestigator
from app.intelligence.provider import MockLLMProvider


def _build_test_rec_result(
    classification: ExceptionType = ExceptionType.AMOUNT_MISMATCH,
    delta: Decimal = Decimal("23.60"),
    is_policy_known: bool = True,
) -> ReconciliationResult:
    monetary = MonetaryEvidence(
        payment_gross=Decimal("1000.00"),
        settled_net=Decimal("976.40"),
        fee_deducted=Decimal("20.00"),
        fee_tax_deducted=Decimal("3.60"),
        total_deductions=Decimal("23.60"),
        settlement_amount_delta=delta,
        standard_contract_fee=Decimal("20.00"),
        standard_contract_fee_tax=Decimal("3.60"),
        fee_variance=Decimal("0.00"),
        tax_variance=Decimal("0.00"),
        is_fee_policy_known=is_policy_known,
    )
    currency = CurrencyEvidence(
        payment_currency="INR",
        settlement_currency="INR",
        ledger_currency="INR",
        is_currency_matched=True,
    )
    timing = TimingEvidence(
        payment_timestamp="2026-08-30T10:00:00Z",
        settlement_timestamp="2026-08-30T14:00:00Z",
        hours_to_settlement=4.0,
        is_within_sla_window=True,
    )
    reference = ReferenceEvidence(
        payment_id="PAY_INV_01",
        settlement_payment_id="PAY_INV_01",
        payment_order_id="ORD_INV_01",
        is_payment_id_matched=True,
        is_order_id_matched=True,
    )
    cardinality = CardinalityEvidence(payment_count=1, settlement_count=1)
    evidence = ReconciliationEvidence(
        monetary=monetary,
        currency=currency,
        timing=timing,
        reference=reference,
        cardinality=cardinality,
    )
    return ReconciliationResult(
        case_id="case_inv_01",
        order_id="ORD_INV_01",
        classification=classification,
        policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        confidence=1.0,
        evidence=evidence,
        reason_code="RULE_FEE_VARIANCE",
        summary="Deterministic fee variance check",
        reconciled_at="2026-08-30T15:00:00Z",
    )


@pytest.mark.asyncio
async def test_investigator_normal_investigation() -> None:
    provider = MockLLMProvider(scenario="correct")
    investigator = AIInvestigator(provider=provider)
    rec_result = _build_test_rec_result()
    policy = FeeTaxPolicy()

    result = await investigator.investigate_case(
        case_id="case_inv_01",
        deterministic_result=rec_result,
        fee_policy=policy,
    )

    assert result.status == InvestigationStatus.INVESTIGATED
    assert result.root_cause_category == RootCauseCategory.PROCESSING_FEE_DEDUCTION
    assert result.confidence_level == ConfidenceLevel.HIGH
    assert len(result.evidence_references) > 0
    assert result.recommended_action == BoundedRecommendation.REVIEW_REQUIRED
    assert result.model_metadata["provider"] == "mock"


@pytest.mark.asyncio
async def test_investigator_unknown_policy_guard() -> None:
    provider = MockLLMProvider(scenario="correct")
    investigator = AIInvestigator(provider=provider)
    rec_result = _build_test_rec_result(is_policy_known=False)

    # Note: no fee_policy provided
    result = await investigator.investigate_case(
        case_id="case_inv_02",
        deterministic_result=rec_result,
        fee_policy=None,
    )

    assert result.status == InvestigationStatus.POLICY_UNAVAILABLE
    assert result.recommended_action == BoundedRecommendation.REVIEW_REQUIRED
    assert "unknown / unconfigured" in str(result.uncertainty_notes)


@pytest.mark.asyncio
async def test_investigator_fallback_on_provider_error() -> None:
    provider = MockLLMProvider(scenario="malformed")
    investigator = AIInvestigator(provider=provider)
    rec_result = _build_test_rec_result()

    result = await investigator.investigate_case(
        case_id="case_inv_03",
        deterministic_result=rec_result,
    )

    assert result.status == InvestigationStatus.UNAVAILABLE
    assert result.root_cause_category == RootCauseCategory.UNIDENTIFIED_ROOT_CAUSE
    assert result.recommended_action == BoundedRecommendation.REVIEW_REQUIRED
    assert result.confidence_score == 0.0
    assert result.model_metadata.get("is_fallback") is True
