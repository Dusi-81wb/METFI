"""
Unit tests for AI Verifier independent validation, hard gates, and rejection mechanics.
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
    EvidenceReference,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerifierStatus,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.intelligence.context_builder import AIContextBuilder
from app.intelligence.provider import MockLLMProvider
from app.intelligence.verifier import AIVerifier


def _build_test_case_context(
    classification: ExceptionType = ExceptionType.AMOUNT_MISMATCH,
    fee_variance: Decimal = Decimal("0.00"),
    is_policy_known: bool = True,
):
    monetary = MonetaryEvidence(
        payment_gross=Decimal("1000.00"),
        settled_net=Decimal("976.40"),
        fee_deducted=Decimal("20.00"),
        fee_tax_deducted=Decimal("3.60"),
        total_deductions=Decimal("23.60"),
        settlement_amount_delta=Decimal("0.00"),
        standard_contract_fee=Decimal("20.00"),
        standard_contract_fee_tax=Decimal("3.60"),
        fee_variance=fee_variance,
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
        payment_id="PAY_VER_01",
        settlement_payment_id="PAY_VER_01",
        payment_order_id="ORD_VER_01",
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
    rec_result = ReconciliationResult(
        case_id="case_ver_01",
        order_id="ORD_VER_01",
        classification=classification,
        policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        confidence=1.0,
        evidence=evidence,
        reason_code="RULE_FEE_VARIANCE",
        summary="Deterministic check",
        reconciled_at="2026-08-30T15:00:00Z",
    )
    policy = FeeTaxPolicy() if is_policy_known else None
    ctx = AIContextBuilder.build_case_context(
        case_id="case_ver_01",
        deterministic_result=rec_result,
        fee_policy=policy,
    )
    return rec_result, ctx


@pytest.mark.asyncio
async def test_verifier_passes_on_valid_investigation() -> None:
    rec_result, ctx = _build_test_case_context()
    investigation = InvestigationResult(
        case_id="case_ver_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Gross and net difference is explained by 2% fee and 18% GST.",
        evidence_references=[
            EvidenceReference(
                field_path="monetary.settlement_amount_delta",
                observed_value="0.00",
                significance="Delta is zero under policy",
            )
        ],
        confidence_level=ConfidenceLevel.HIGH,
        confidence_score=0.95,
        recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
    )

    verifier = AIVerifier(provider=MockLLMProvider(scenario="correct"))
    ver_res = await verifier.verify_investigation(
        case_id="case_ver_01",
        deterministic_result=rec_result,
        investigation=investigation,
        case_context=ctx,
    )

    assert ver_res.verifier_status == VerifierStatus.VERIFIED
    assert ver_res.is_evidence_supported is True
    assert ver_res.are_references_valid is True
    assert ver_res.is_deterministic_truth_preserved is True
    assert ver_res.is_recommendation_safe is True
    assert len(ver_res.rejection_reasons) == 0


@pytest.mark.asyncio
async def test_verifier_rejects_hallucinated_citations() -> None:
    rec_result, ctx = _build_test_case_context()
    investigation = InvestigationResult(
        case_id="case_ver_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Unsupported claim citing non-existent fields.",
        evidence_references=[
            EvidenceReference(
                field_path="nonexistent.fabricated_discount_rate",
                observed_value="5.0%",
                significance="[UNCERTIFIED PATH] Fabricated citation",
            )
        ],
        recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
    )

    verifier = AIVerifier(provider=MockLLMProvider(scenario="correct"))
    ver_res = await verifier.verify_investigation(
        case_id="case_ver_01",
        deterministic_result=rec_result,
        investigation=investigation,
        case_context=ctx,
    )

    assert ver_res.verifier_status == VerifierStatus.REJECTED
    assert ver_res.are_references_valid is False
    assert any("Invalid evidence citation" in r for r in ver_res.rejection_reasons)


@pytest.mark.asyncio
async def test_verifier_rejects_deterministic_override_attempt() -> None:
    # Currency mismatch case where AI attempts to recommend AUTO_RECONCILE
    rec_result, ctx = _build_test_case_context(classification=ExceptionType.CURRENCY_MISMATCH)
    investigation = InvestigationResult(
        case_id="case_ver_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.CURRENCY_CONVERSION_VARIANCE,
        primary_explanation="Currency mismatch identified.",
        evidence_references=[],
        recommended_action=BoundedRecommendation.AUTO_RECONCILE,  # Violation!
    )

    verifier = AIVerifier(provider=MockLLMProvider(scenario="correct"))
    ver_res = await verifier.verify_investigation(
        case_id="case_ver_01",
        deterministic_result=rec_result,
        investigation=investigation,
        case_context=ctx,
    )

    assert ver_res.verifier_status == VerifierStatus.REJECTED
    assert ver_res.is_deterministic_truth_preserved is False
    assert any("blocking: CURRENCY_MISMATCH" in r for r in ver_res.rejection_reasons)


@pytest.mark.asyncio
async def test_verifier_rejects_auto_reconcile_with_fee_variance() -> None:
    # Fee variance exists, AI tries to AUTO_RECONCILE
    rec_result, ctx = _build_test_case_context(fee_variance=Decimal("15.00"))
    investigation = InvestigationResult(
        case_id="case_ver_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Fee variance present.",
        evidence_references=[],
        recommended_action=BoundedRecommendation.AUTO_RECONCILE,  # Violation!
    )

    verifier = AIVerifier(provider=MockLLMProvider(scenario="correct"))
    ver_res = await verifier.verify_investigation(
        case_id="case_ver_01",
        deterministic_result=rec_result,
        investigation=investigation,
        case_context=ctx,
    )

    assert ver_res.verifier_status == VerifierStatus.REJECTED
    assert ver_res.is_recommendation_safe is False
    assert any("with variance" in r for r in ver_res.rejection_reasons)
