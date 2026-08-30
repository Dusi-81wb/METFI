"""
Unit tests for AI Benchmark Evaluator and multi-tier comparative reporting.
"""

from decimal import Decimal

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    EvidenceReference,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.evaluation.ai_evaluator import AIIssueEvaluator


def _create_mock_envelope(
    case_id: str,
    classification: ExceptionType,
    root_cause: RootCauseCategory,
    verifier_status: VerifierStatus = VerifierStatus.VERIFIED,
) -> VerifiedInvestigationEnvelope:
    monetary = MonetaryEvidence(payment_gross=Decimal("100.00"), settled_net=Decimal("97.64"))
    currency = CurrencyEvidence(payment_currency="INR", is_currency_matched=True)
    timing = TimingEvidence(is_within_sla_window=True)
    reference = ReferenceEvidence(payment_id=f"PAY_{case_id}")
    cardinality = CardinalityEvidence(payment_count=1, settlement_count=1)
    ev = ReconciliationEvidence(
        monetary=monetary,
        currency=currency,
        timing=timing,
        reference=reference,
        cardinality=cardinality,
    )
    rec = ReconciliationResult(
        case_id=case_id,
        order_id=f"ORD_{case_id}",
        classification=classification,
        policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        confidence=1.0,
        evidence=ev,
        reason_code="RULE_TEST",
        summary="Test",
        reconciled_at="2026-08-30T15:00:00Z",
    )
    inv = InvestigationResult(
        case_id=case_id,
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=root_cause,
        primary_explanation="Explanation grounded in evidence.",
        evidence_references=[
            EvidenceReference(
                field_path="monetary.settled_net",
                observed_value="97.64",
                significance="Observed net payout",
            )
        ],
        confidence_level=ConfidenceLevel.HIGH,
        confidence_score=0.95,
        recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
    )
    ver = VerificationResult(
        investigation_id=inv.investigation_id,
        case_id=case_id,
        verifier_status=verifier_status,
        is_evidence_supported=(verifier_status == VerifierStatus.VERIFIED),
        are_references_valid=True,
        is_deterministic_truth_preserved=True,
        is_recommendation_safe=True,
        verifier_notes="Verified",
    )
    return VerifiedInvestigationEnvelope(
        case_id=case_id,
        deterministic_result=rec,
        investigation=inv,
        verification=ver,
        final_canonical_status=classification,
        final_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        summary="Summary test",
    )


def test_ai_evaluator_empty_set() -> None:
    report = AIIssueEvaluator.evaluate_envelopes([])
    assert report.metrics.total_cases_evaluated == 0
    assert report.metrics.deterministic_preservation_rate == 1.0


def test_ai_evaluator_metrics_calculation() -> None:
    envelopes = [
        _create_mock_envelope(
            "case_1", ExceptionType.AMOUNT_MISMATCH, RootCauseCategory.PROCESSING_FEE_DEDUCTION
        ),
        _create_mock_envelope(
            "case_2",
            ExceptionType.CURRENCY_MISMATCH,
            RootCauseCategory.CURRENCY_CONVERSION_VARIANCE,
        ),
        _create_mock_envelope(
            "case_3",
            ExceptionType.AMOUNT_MISMATCH,
            RootCauseCategory.PROCESSING_FEE_DEDUCTION,
            VerifierStatus.REJECTED,
        ),
    ]
    gt_map = {
        "case_1": {"expected_root_cause": "PROCESSING_FEE_DEDUCTION"},
        "case_2": {"expected_root_cause": "CURRENCY_CONVERSION_VARIANCE"},
        "case_3": {"expected_root_cause": "PROCESSING_FEE_DEDUCTION"},
    }

    report = AIIssueEvaluator.evaluate_envelopes(
        envelopes, ground_truth_map=gt_map, dataset_id="test_set"
    )

    assert report.metrics.total_cases_evaluated == 3
    assert report.metrics.root_cause_accuracy == 1.0
    assert report.metrics.deterministic_preservation_rate == 1.0
    assert round(report.metrics.verifier_rejection_rate, 2) == 0.33
    assert round(report.metrics.evidence_grounding_rate, 2) == 0.67
