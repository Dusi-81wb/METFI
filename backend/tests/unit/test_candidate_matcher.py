"""Unit tests for CandidateMatcher candidate generation and multi-source grouping."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.enums import LedgerAccount, LedgerStatus, PaymentStatus, SettlementStatus
from app.reconciliation.candidate_matcher import CandidateMatcher, _levenshtein_distance


def _make_payment(payment_id: str, order_id: str, amount: str = "100.00") -> CanonicalPayment:
    return CanonicalPayment(
        payment_id=payment_id,
        order_id=order_id,
        customer_id="cust_001",
        amount=Decimal(amount),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
        metadata={},
    )


def _make_settlement(
    settlement_id: str, payment_id: str, settled_amount: str = "98.00"
) -> CanonicalSettlement:
    return CanonicalSettlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        settled_amount=Decimal(settled_amount),
        fee=Decimal("1.69"),
        fee_tax=Decimal("0.31"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 12, 0, 0, tzinfo=UTC),
        status=SettlementStatus.SETTLED,
        metadata={},
    )


def _make_ledger_pair(order_id: str, amount: str = "100.00") -> list[CanonicalLedgerEntry]:
    return [
        CanonicalLedgerEntry(
            ledger_id=f"led_dr_{order_id}",
            order_id=order_id,
            debit=Decimal(amount),
            credit=Decimal("0.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
            account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
        CanonicalLedgerEntry(
            ledger_id=f"led_cr_{order_id}",
            order_id=order_id,
            debit=Decimal("0.00"),
            credit=Decimal(amount),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
            account=LedgerAccount.ACCOUNTS_RECEIVABLE,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
    ]


def test_levenshtein_distance() -> None:
    assert _levenshtein_distance("ord_12345", "ord_12345") == 0
    assert _levenshtein_distance("ord_12345", "ord_1234X") == 1
    assert _levenshtein_distance("abc", "def") == 3


def test_exact_candidate_linkage() -> None:
    matcher = CandidateMatcher()
    payment = _make_payment("pay_01", "ord_01")
    settlement = _make_settlement("set_01", "pay_01")
    ledger = _make_ledger_pair("ord_01")

    groups = matcher.group_candidates([payment], [settlement], ledger)

    assert len(groups) == 1
    g = groups[0]
    assert g.order_id == "ord_01"
    assert g.payment is not None and g.payment.payment_id == "pay_01"
    assert g.settlement is not None and g.settlement.settlement_id == "set_01"
    assert len(g.ledger_entries) == 2


def test_duplicate_settlement_linkage() -> None:
    matcher = CandidateMatcher()
    payment = _make_payment("pay_02", "ord_02")
    s1 = _make_settlement("set_02a", "pay_02")
    s2 = _make_settlement("set_02b", "pay_02")
    ledger = _make_ledger_pair("ord_02")

    groups = matcher.group_candidates([payment], [s1, s2], ledger)

    assert len(groups) == 1
    g = groups[0]
    assert g.payment is not None and g.payment.payment_id == "pay_02"
    assert g.settlement is not None and g.settlement.settlement_id == "set_02a"


def test_missing_settlement_grouping() -> None:
    matcher = CandidateMatcher()
    payment = _make_payment("pay_03", "ord_03")
    ledger = _make_ledger_pair("ord_03")

    groups = matcher.group_candidates([payment], [], ledger)

    assert len(groups) == 1
    g = groups[0]
    assert g.payment is not None
    assert g.settlement is None
    assert len(g.ledger_entries) == 2


def test_reference_mismatch_fuzzy_linkage() -> None:
    matcher = CandidateMatcher()
    payment = _make_payment("pay_04", "ord_abcd_1234")
    settlement = _make_settlement("set_04", "pay_04")
    # Mutate 1 character in ledger order ID
    ledger = _make_ledger_pair("ord_abcd_123X")

    groups = matcher.group_candidates([payment], [settlement], ledger)

    assert len(groups) == 1
    g = groups[0]
    assert g.order_id == "ord_abcd_1234"
    assert g.payment is not None
    assert g.settlement is not None
    assert len(g.ledger_entries) == 2
    assert g.ledger_entries[0].order_id == "ord_abcd_123X"
