"""Unit tests for BenchmarkEvaluator metric computations and confusion matrix generation."""

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
from app.domain.ground_truth import GroundTruthRecord
from app.domain.reconciliation_result import ReconciliationResult
from app.evaluation.evaluator import BenchmarkEvaluator


def _make_dummy_evidence() -> ReconciliationEvidence:
    return ReconciliationEvidence(
        monetary=MonetaryEvidence(),
        currency=CurrencyEvidence(),
        timing=TimingEvidence(),
        reference=ReferenceEvidence(),
        cardinality=CardinalityEvidence(),
    )


def test_evaluator_perfect_accuracy() -> None:
    evaluator = BenchmarkEvaluator()

    results = [
        ReconciliationResult(
            case_id="case_1",
            order_id="ord_1",
            classification=ExceptionType.EXACT_MATCH,
            policy_outcome=PolicyOutcome.AUTO_RECONCILE,
            evidence=_make_dummy_evidence(),
            reason_code="EXACT_MATCH_VERIFIED",
            summary="Clean",
            reconciled_at="2026-08-01T00:00:00Z",
        ),
        ReconciliationResult(
            case_id="case_2",
            order_id="ord_2",
            classification=ExceptionType.AMOUNT_MISMATCH,
            policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
            evidence=_make_dummy_evidence(),
            reason_code="DELTA",
            summary="Mismatch",
            reconciled_at="2026-08-01T00:00:00Z",
        ),
    ]

    ground_truth = [
        GroundTruthRecord(
            case_id="case_1",
            order_id="ord_1",
            expected_classification=ExceptionType.EXACT_MATCH,
            expected_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        ),
        GroundTruthRecord(
            case_id="case_2",
            order_id="ord_2",
            expected_classification=ExceptionType.AMOUNT_MISMATCH,
            expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        ),
    ]

    report = evaluator.evaluate(results, ground_truth, dataset_id="test_set")

    assert report.overall_accuracy == 1.0
    assert report.correct_classifications == 2
    assert report.false_match_rate == 0.0
    assert len(report.failures) == 0
    assert report.per_class_metrics["EXACT_MATCH"].precision == 1.0
    assert report.per_class_metrics["AMOUNT_MISMATCH"].recall == 1.0


def test_evaluator_captures_misclassifications() -> None:
    evaluator = BenchmarkEvaluator()

    # Model predicted EXACT_MATCH for an AMOUNT_MISMATCH exception case
    results = [
        ReconciliationResult(
            case_id="case_3",
            order_id="ord_3",
            classification=ExceptionType.EXACT_MATCH,
            policy_outcome=PolicyOutcome.AUTO_RECONCILE,
            evidence=_make_dummy_evidence(),
            reason_code="EXACT_MATCH_VERIFIED",
            summary="False pass",
            reconciled_at="2026-08-01T00:00:00Z",
        ),
    ]

    ground_truth = [
        GroundTruthRecord(
            case_id="case_3",
            order_id="ord_3",
            expected_classification=ExceptionType.AMOUNT_MISMATCH,
            expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
            expected_amount_delta=Decimal("50.00"),
        ),
    ]

    report = evaluator.evaluate(results, ground_truth, dataset_id="test_set_fail")

    assert report.overall_accuracy == 0.0
    assert report.false_match_rate == 1.0  # False match rate triggered
    assert len(report.failures) == 1
    assert report.failures[0].actual_class == "AMOUNT_MISMATCH"
    assert report.failures[0].predicted_class == "EXACT_MATCH"
