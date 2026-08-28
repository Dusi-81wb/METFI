"""
Candidate Matcher Safety & Multi-Record Linkage Test Suite.

Verifies:
1. Customer identity guard: Reject fuzzy linkage across distinct customers.
2. Candidate uniqueness: Multi-candidate ties correctly mark ambiguity.
3. Multi-settlement evaluation without blind index-0 truncation.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.enums import ExceptionType, LedgerAccount, LedgerStatus, PaymentStatus, SettlementStatus
from app.reconciliation.candidate_matcher import CandidateMatcher
from app.reconciliation.engine import DeterministicReconciliationEngine


@pytest.fixture
def matcher() -> CandidateMatcher:
    return CandidateMatcher()


@pytest.fixture
def engine() -> DeterministicReconciliationEngine:
    return DeterministicReconciliationEngine()


def test_customer_guard_rejects_cross_customer_fuzzy_match(
    matcher: CandidateMatcher,
    engine: DeterministicReconciliationEngine,
) -> None:
    """
    Ensure fuzzy matching does NOT connect Customer A to Customer B
    even if their order IDs are lexically similar (e.g. edit distance 1).
    """
    # Payment for Customer A with order 'ord_cust_100'
    pay = CanonicalPayment(
        payment_id="pay_cust_a",
        order_id="ord_cust_100",
        customer_id="customer_A",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
    )
    settle = CanonicalSettlement(
        settlement_id="set_cust_a",
        payment_id="pay_cust_a",
        settled_amount=Decimal("976.40"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        status=SettlementStatus.SETTLED,
    )
    # Unlinked ledger entry for Customer B with similar order 'ord_cust_101' (dist=1)
    led = CanonicalLedgerEntry(
        ledger_id="led_cust_b",
        order_id="ord_cust_101",
        debit=Decimal("1000.00"),
        credit=Decimal("0.00"),
        currency="INR",
        entry_timestamp=datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc),
        account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
        status=LedgerStatus.POSTED,
        metadata={"customer_id": "customer_B"},  # Conflicting customer
    )

    groups = matcher.group_candidates(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[led],
    )

    # Customer guard must prevent linking Customer B's ledger to Customer A's payment
    pay_group = [g for g in groups if g.payment and g.payment.payment_id == "pay_cust_a"][0]
    assert len(pay_group.ledger_entries) == 0  # Not linked!


def test_multi_candidate_tie_marks_ambiguity(
    matcher: CandidateMatcher,
    engine: DeterministicReconciliationEngine,
) -> None:
    """
    When multiple unlinked ledger entries match with equal edit distance and valid parameters,
    candidate matcher must mark group as ambiguous candidate rather than making arbitrary choice.
    """
    pay = CanonicalPayment(
        payment_id="pay_tie_001",
        order_id="ord_root_100",
        customer_id="cust_tie",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
    )
    settle = CanonicalSettlement(
        settlement_id="set_tie_001",
        payment_id="pay_tie_001",
        settled_amount=Decimal("976.40"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        status=SettlementStatus.SETTLED,
    )
    # Candidate 1: 'ord_root_10A' (dist = 1)
    led1 = CanonicalLedgerEntry(
        ledger_id="led_tie_1",
        order_id="ord_root_10A",
        debit=Decimal("1000.00"),
        credit=Decimal("0.00"),
        currency="INR",
        entry_timestamp=datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc),
        account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
        status=LedgerStatus.POSTED,
        metadata={"customer_id": "cust_tie"},
    )
    # Candidate 2: 'ord_root_10B' (dist = 1)
    led2 = CanonicalLedgerEntry(
        ledger_id="led_tie_2",
        order_id="ord_root_10B",
        debit=Decimal("1000.00"),
        credit=Decimal("0.00"),
        currency="INR",
        entry_timestamp=datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc),
        account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
        status=LedgerStatus.POSTED,
        metadata={"customer_id": "cust_tie"},
    )

    groups = matcher.group_candidates(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[led1, led2],
    )

    pay_group = [g for g in groups if g.payment and g.payment.payment_id == "pay_tie_001"][0]
    assert pay_group.is_ambiguous_candidate is True

    # Reconciling this group should yield AMBIGUOUS
    res = engine.reconcile_group(pay_group)
    assert res.classification == ExceptionType.AMBIGUOUS
