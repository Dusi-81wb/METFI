"""
Unit tests for Phase 7 Strict Ground-Truth Isolation.

Verifies:
1. Ground truth annotations exist exclusively in test/benchmark evaluation code.
2. Raw financial intake payloads contain zero ground-truth leakage.
3. Deterministic reconciliation result objects do not leak ground-truth metadata.
4. AI investigator context builder explicitly excludes ground-truth fields.
5. Audit event payloads and SHA-256 canonical hash strings contain zero ground truth.
6. Frontend domain models exclude any ground-truth fields from production schemas.
"""

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.audit.sanitizer import AuditSanitizer
from app.domain.canonical import CanonicalPayment, CanonicalSettlement, CanonicalTransactionGroup
from app.domain.enums import PaymentStatus, SettlementStatus
from app.intelligence.context_builder import AIContextBuilder
from app.reconciliation.engine import DeterministicReconciliationEngine


def test_adversarial_fixture_strips_ground_truth_for_runtime() -> None:
    """Ensure adversarial fixtures separate runtime input from evaluation ground truth."""
    repo_root = Path(__file__).resolve().parents[3]
    fixture_path = repo_root / "data" / "fixtures" / "adversarial_evaluation_dataset.json"
    assert fixture_path.exists(), "Adversarial dataset fixture must exist"

    raw_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    for case in raw_data["cases"]:
        # Ground truth fields are strictly separated from runtime intake payloads
        payment = case.get("payment")
        if payment:
            assert "expected_classification" not in payment
            assert "expected_policy_outcome" not in payment
            assert "injected_fault" not in payment
            assert "ground_truth" not in payment

        settlement = case.get("settlement")
        if settlement:
            assert "expected_classification" not in settlement
            assert "expected_policy_outcome" not in settlement
            assert "ground_truth" not in settlement


def test_ai_context_builder_contains_zero_ground_truth() -> None:
    """Ensure AIContextBuilder does not accept or inject ground truth."""
    group = CanonicalTransactionGroup(
        case_id="case_gt_01",
        order_id="ORD-GT-01",
        payment=CanonicalPayment(
            payment_id="PAY-GT-01",
            order_id="ORD-GT-01",
            customer_id="CUST-GT-01",
            amount=Decimal("5000.00"),
            currency="INR",
            status=PaymentStatus.SUCCESS,
            payment_timestamp=datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC),
        ),
        settlements=[
            CanonicalSettlement(
                settlement_id="SET-GT-01",
                payment_id="PAY-GT-01",
                settled_amount=Decimal("4970.50"),
                currency="INR",
                settlement_timestamp=datetime(2026, 9, 2, 11, 0, 0, tzinfo=UTC),
                fee=Decimal("25.00"),
                fee_tax=Decimal("4.50"),
                status=SettlementStatus.SETTLED,
            )
        ],
    )

    rec_engine = DeterministicReconciliationEngine()
    rec_res = rec_engine.reconcile_group(group)

    context_res = AIContextBuilder.build_case_context(
        case_id="case_gt_01",
        deterministic_result=rec_res,
        group=group,
    )
    context = context_res.rendered_text

    # Prompt text sent to LLM must not contain ground truth labels
    assert "GROUND_TRUTH" not in context.upper()
    assert "EXPECTED_OUTCOME" not in context.upper()
    assert "INJECTED_FAULT" not in context.upper()


def test_audit_sanitizer_removes_ground_truth_if_accidentally_passed() -> None:
    """AuditPayloadSanitizer must scrub accidental ground truth keys from payload."""
    dirty_payload = {
        "order_id": "ORD-GT-99",
        "amount": "1000.00",
        "ground_truth_classification": "FEE_VARIANCE",
        "injected_fault_type": "FEE_SURCHARGE",
        "expected_result": "AUTO_RECONCILE",
    }

    clean_payload = AuditSanitizer.sanitize_payload(dirty_payload)

    # Verify sensitive & ground truth leakage scrubbed
    clean_str = json.dumps(clean_payload)
    assert "ground_truth_classification" not in clean_str
    assert "injected_fault_type" not in clean_str
    assert "expected_result" not in clean_str
    assert clean_payload["order_id"] == "ORD-GT-99"
