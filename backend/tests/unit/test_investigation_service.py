"""
Unit tests for InvestigationService end-to-end orchestration and batch processing.
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
    InvestigationStatus,
    VerifierStatus,
)
from app.domain.reconciliation_result import (
    BatchPerformanceMetrics,
    BatchReconciliationResult,
    ReconciliationResult,
)
from app.intelligence.provider import MockLLMProvider
from app.services.investigation_service import InvestigationService


def _build_test_result(
    case_id: str,
    classification: ExceptionType,
    policy_outcome: PolicyOutcome = PolicyOutcome.REVIEW_REQUIRED,
) -> ReconciliationResult:
    monetary = MonetaryEvidence(
        payment_gross=Decimal("100.00"),
        settled_net=Decimal("97.64"),
        settlement_amount_delta=Decimal("0.00"),
    )
    currency = CurrencyEvidence(
        payment_currency="INR", settlement_currency="INR", is_currency_matched=True
    )
    timing = TimingEvidence(is_within_sla_window=True)
    reference = ReferenceEvidence(payment_id=f"PAY_{case_id}")
    cardinality = CardinalityEvidence(payment_count=1, settlement_count=1)
    evidence = ReconciliationEvidence(
        monetary=monetary,
        currency=currency,
        timing=timing,
        reference=reference,
        cardinality=cardinality,
    )
    return ReconciliationResult(
        case_id=case_id,
        order_id=f"ORD_{case_id}",
        classification=classification,
        policy_outcome=policy_outcome,
        confidence=1.0,
        evidence=evidence,
        reason_code="RULE_TEST",
        summary="Test summary",
        reconciled_at="2026-08-30T15:00:00Z",
    )


@pytest.mark.asyncio
async def test_exact_match_triage_bypass() -> None:
    service = InvestigationService(provider=MockLLMProvider())
    rec = _build_test_result("case_exact", ExceptionType.EXACT_MATCH, PolicyOutcome.AUTO_RECONCILE)

    env = await service.investigate_case(case_id="case_exact", deterministic_result=rec)

    assert env.final_canonical_status == ExceptionType.EXACT_MATCH
    assert env.final_policy_outcome == PolicyOutcome.AUTO_RECONCILE
    assert env.verification.verifier_status == VerifierStatus.VERIFIED
    assert env.investigation.model_metadata.get("triage") == "exact_match_bypass"


@pytest.mark.asyncio
async def test_investigate_exception_case() -> None:
    service = InvestigationService(provider=MockLLMProvider(scenario="correct"))
    rec = _build_test_result(
        "case_mismatch", ExceptionType.AMOUNT_MISMATCH, PolicyOutcome.REVIEW_REQUIRED
    )

    env = await service.investigate_case(
        case_id="case_mismatch",
        deterministic_result=rec,
        fee_policy=FeeTaxPolicy(),
    )

    assert env.final_canonical_status == ExceptionType.AMOUNT_MISMATCH
    assert env.final_policy_outcome == PolicyOutcome.REVIEW_REQUIRED
    assert env.verification.verifier_status == VerifierStatus.VERIFIED
    assert env.investigation.status == InvestigationStatus.INVESTIGATED


@pytest.mark.asyncio
async def test_investigate_batch_execution() -> None:
    service = InvestigationService(provider=MockLLMProvider(scenario="correct"))
    results = [
        _build_test_result(
            f"case_{i}", ExceptionType.AMOUNT_MISMATCH, PolicyOutcome.REVIEW_REQUIRED
        )
        for i in range(5)
    ]
    batch_res = BatchReconciliationResult(
        dataset_id="test_batch",
        total_cases=5,
        results=results,
        class_distribution={"AMOUNT_MISMATCH": 5},
        policy_distribution={"REVIEW_REQUIRED": 5},
        performance_metrics=BatchPerformanceMetrics(
            total_records_processed=10,
            total_cases_reconciled=5,
            candidate_generation_time_ms=1.0,
            evidence_and_classification_time_ms=2.0,
            total_wall_clock_time_ms=3.0,
            throughput_records_per_sec=1000.0,
            latency_p50_ms=0.5,
            latency_p95_ms=0.8,
            latency_p99_ms=0.9,
        ),
    )

    envelopes = await service.investigate_batch(batch_res, fee_policy=FeeTaxPolicy())
    assert len(envelopes) == 5
    for env in envelopes:
        assert env.final_canonical_status == ExceptionType.AMOUNT_MISMATCH
        assert env.verification.verifier_status == VerifierStatus.VERIFIED
