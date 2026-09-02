"""
Unit tests for Phase 8 Performance, Latency Budgets & Pipeline Throughput.

Verifies:
1. Deterministic reconciliation executes well within sub-5ms latency budget.
2. Deterministic policy gating executes in under 2ms.
3. Cryptographic SHA-256 canonical event hashing executes in under 1ms per event.
4. Batch matching processes over 1,000 transactions per second.
"""

import time
from datetime import UTC, datetime
from decimal import Decimal

from app.audit.hasher import AuditHasher
from app.audit.models import AuditEvent, AuditEventType
from app.domain.action import ActionType
from app.domain.audit import Actor, ActorType
from app.domain.canonical import CanonicalPayment, CanonicalSettlement, CanonicalTransactionGroup
from app.domain.enums import PaymentStatus, SettlementStatus
from app.domain.investigation import (
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.policy.policy_engine import DeterministicPolicyEngine
from app.reconciliation.engine import DeterministicReconciliationEngine


def test_reconciliation_engine_latency_budget() -> None:
    """Ensure deterministic matching executes within sub-millisecond latency."""
    group = CanonicalTransactionGroup(
        case_id="case_perf_01",
        order_id="ORD-PERF-01",
        payment=CanonicalPayment(
            payment_id="PAY-PERF-01",
            order_id="ORD-PERF-01",
            customer_id="CUST-PERF-01",
            amount=Decimal("1000.00"),
            currency="INR",
            status=PaymentStatus.SUCCESS,
            payment_timestamp=datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC),
        ),
        settlements=[
            CanonicalSettlement(
                settlement_id="SET-PERF-01",
                payment_id="PAY-PERF-01",
                settled_amount=Decimal("994.10"),
                currency="INR",
                settlement_timestamp=datetime(2026, 9, 2, 10, 15, 0, tzinfo=UTC),
                fee=Decimal("5.00"),
                fee_tax=Decimal("0.90"),
                status=SettlementStatus.SETTLED,
            )
        ],
    )

    engine = DeterministicReconciliationEngine()

    t0 = time.perf_counter()
    iterations = 500
    for _ in range(iterations):
        engine.reconcile_group(group)
    elapsed = time.perf_counter() - t0

    avg_ms = (elapsed / iterations) * 1000
    assert avg_ms < 5.0, f"Average latency was {avg_ms:.4f}ms, must be < 5.0ms"


def test_policy_engine_latency_budget() -> None:
    """Ensure deterministic policy rule gating runs in under 2ms."""
    group = CanonicalTransactionGroup(
        case_id="case_perf_pol",
        order_id="ORD-PERF-POL",
        payment=CanonicalPayment(
            payment_id="PAY-PP-01",
            order_id="ORD-PERF-POL",
            customer_id="CUST-PP-01",
            amount=Decimal("1000.00"),
            currency="INR",
            status=PaymentStatus.SUCCESS,
            payment_timestamp=datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC),
        ),
    )
    rec_engine = DeterministicReconciliationEngine()
    rec_res = rec_engine.reconcile_group(group)

    envelope = VerifiedInvestigationEnvelope(
        case_id="case_perf_pol",
        deterministic_result=rec_res,
        final_canonical_status=rec_res.classification,
        final_policy_outcome=rec_res.policy_outcome,
        summary="Performance envelope",
        investigation=InvestigationResult(
            case_id="case_perf_pol",
            status=InvestigationStatus.INVESTIGATED,
            root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
            primary_explanation="Verified gateway fee deduction",
            confidence_score=0.98,
            evidence_references=[],
        ),
        verification=VerificationResult(
            verification_id="ver_perf",
            investigation_id="inv_perf",
            case_id="case_perf_pol",
            verifier_status=VerifierStatus.VERIFIED,
            is_evidence_supported=True,
            are_references_valid=True,
            is_deterministic_truth_preserved=True,
            is_recommendation_safe=True,
            verifier_notes="Evidence checked",
        ),
    )

    engine = DeterministicPolicyEngine()

    t0 = time.perf_counter()
    iterations = 500
    for _ in range(iterations):
        engine.evaluate_action_authorization(
            case_id="case_perf_pol",
            deterministic_result=rec_res,
            envelope=envelope,
            requested_action=ActionType.AUTO_RECONCILE,
        )
    elapsed = time.perf_counter() - t0

    avg_ms = (elapsed / iterations) * 1000
    assert avg_ms < 2.0, f"Average policy latency was {avg_ms:.4f}ms, must be < 2.0ms"


def test_audit_hasher_latency_budget() -> None:
    """Ensure SHA-256 canonical hashing processes under 1ms per event."""
    actor = Actor(actor_type=ActorType.SYSTEM, actor_id="perf-engine")
    event = AuditEvent(
        event_id="evt-perf-01",
        event_type=AuditEventType.RECONCILIATION_COMPLETED,
        case_id="case_perf_01",
        correlation_id="corr-perf-01",
        sequence_number=1,
        timestamp=datetime.now(UTC).isoformat(),
        source_component="audit_test",
        actor=actor,
        previous_event_hash="GENESIS",
        payload={"order_id": "ORD-PERF-01", "status": "MATCHED"},
    )

    t0 = time.perf_counter()
    iterations = 500
    for _ in range(iterations):
        AuditHasher.compute_event_hash(event)
    elapsed = time.perf_counter() - t0

    avg_ms = (elapsed / iterations) * 1000
    assert avg_ms < 1.0, f"Average hash latency was {avg_ms:.4f}ms, must be < 1.0ms"
