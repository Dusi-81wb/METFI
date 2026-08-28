"""Unit tests for DeterministicReconciliationEngine across all 10 canonical exception classes."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
    CanonicalTransactionGroup,
)
from app.domain.enums import (
    ExceptionType,
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    PolicyOutcome,
    SettlementStatus,
)
from app.reconciliation.engine import DeterministicReconciliationEngine


def _setup_baseline() -> tuple[CanonicalPayment, CanonicalSettlement, list[CanonicalLedgerEntry]]:
    p = CanonicalPayment(
        payment_id="pay_base",
        order_id="ord_base",
        customer_id="cust_base",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
        metadata={},
    )
    s = CanonicalSettlement(
        settlement_id="set_base",
        payment_id="pay_base",
        settled_amount=Decimal("976.40"),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 12, 0, 0, tzinfo=UTC),
        status=SettlementStatus.SETTLED,
        metadata={},
    )
    led = [
        CanonicalLedgerEntry(
            ledger_id="led_dr_base",
            order_id="ord_base",
            debit=Decimal("1000.00"),
            credit=Decimal("0.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
            account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
        CanonicalLedgerEntry(
            ledger_id="led_cr_base",
            order_id="ord_base",
            debit=Decimal("0.00"),
            credit=Decimal("1000.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC),
            account=LedgerAccount.ACCOUNTS_RECEIVABLE,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
    ]
    return p, s, led


def test_reconcile_exact_match() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    group = CanonicalTransactionGroup(
        case_id="case_01", order_id="ord_base", payment=p, settlement=s, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.EXACT_MATCH
    assert res.policy_outcome == PolicyOutcome.AUTO_RECONCILE
    assert res.confidence == 1.0


def test_reconcile_amount_mismatch() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    s_mutated = s.model_copy(update={"settled_amount": Decimal("900.00")})
    group = CanonicalTransactionGroup(
        case_id="case_02", order_id="ord_base", payment=p, settlement=s_mutated, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.AMOUNT_MISMATCH
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_missing_settlement() -> None:
    engine = DeterministicReconciliationEngine()
    p, _, led = _setup_baseline()
    group = CanonicalTransactionGroup(
        case_id="case_03", order_id="ord_base", payment=p, settlement=None, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.MISSING_SETTLEMENT
    assert res.policy_outcome == PolicyOutcome.UNRESOLVED


def test_reconcile_duplicate_record() -> None:
    engine = DeterministicReconciliationEngine()
    p, s1, led = _setup_baseline()
    s2 = s1.model_copy(update={"settlement_id": "set_base_dup"})
    group = CanonicalTransactionGroup(
        case_id="case_04", order_id="ord_base", payment=p, settlement=s1, ledger_entries=led
    )

    res = engine.reconcile_group(group, all_matched_settlements=[s1, s2])
    assert res.classification == ExceptionType.DUPLICATE_RECORD
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_date_mismatch() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    # Settlement precedes payment by 2 days
    s_preceding = s.model_copy(
        update={"settlement_timestamp": p.payment_timestamp - timedelta(days=2)}
    )
    group = CanonicalTransactionGroup(
        case_id="case_05",
        order_id="ord_base",
        payment=p,
        settlement=s_preceding,
        ledger_entries=led,
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.DATE_MISMATCH
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_reference_mismatch() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    mutated_led = [le.model_copy(update={"order_id": "ord_mutated"}) for le in led]
    group = CanonicalTransactionGroup(
        case_id="case_06", order_id="ord_base", payment=p, settlement=s, ledger_entries=mutated_led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.REFERENCE_MISMATCH
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_partial_settlement() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    # Exactly half payout: 976.40 / 2 = 488.20
    s_partial = s.model_copy(update={"settled_amount": Decimal("488.20")})
    group = CanonicalTransactionGroup(
        case_id="case_07", order_id="ord_base", payment=p, settlement=s_partial, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.PARTIAL_SETTLEMENT
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_fee_discrepancy() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    # 6% fee schedule instead of 2%
    s_fee = s.model_copy(
        update={
            "fee": Decimal("60.00"),
            "fee_tax": Decimal("3.60"),
            "settled_amount": Decimal("936.40"),
        }
    )
    group = CanonicalTransactionGroup(
        case_id="case_08", order_id="ord_base", payment=p, settlement=s_fee, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.FEE_DISCREPANCY
    assert res.policy_outcome == PolicyOutcome.REVIEW_REQUIRED


def test_reconcile_currency_mismatch() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    s_curr = s.model_copy(update={"currency": "USD"})
    group = CanonicalTransactionGroup(
        case_id="case_09", order_id="ord_base", payment=p, settlement=s_curr, ledger_entries=led
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.CURRENCY_MISMATCH
    assert res.policy_outcome == PolicyOutcome.UNRESOLVED


def test_reconcile_ambiguous() -> None:
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_baseline()
    # Structural ambiguity: candidate tie prevents safe unique resolution
    group = CanonicalTransactionGroup(
        case_id="case_10",
        order_id="ord_base",
        payment=p,
        settlement=s,
        ledger_entries=led,
        is_ambiguous_candidate=True,
    )

    res = engine.reconcile_group(group)
    assert res.classification == ExceptionType.AMBIGUOUS
    assert res.policy_outcome == PolicyOutcome.UNRESOLVED
