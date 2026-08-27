"""Unit tests verifying classification precedence hierarchy under multi-fault conditions."""

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
    SettlementStatus,
)
from app.reconciliation.engine import DeterministicReconciliationEngine


def _setup_base_transaction() -> tuple[
    CanonicalPayment, CanonicalSettlement, list[CanonicalLedgerEntry]
]:
    p = CanonicalPayment(
        payment_id="pay_prec",
        order_id="ord_prec",
        customer_id="cust_prec",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
        metadata={},
    )
    s = CanonicalSettlement(
        settlement_id="set_prec_1",
        payment_id="pay_prec",
        settled_amount=Decimal("976.40"),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, 0, tzinfo=UTC),
        status=SettlementStatus.SETTLED,
        metadata={},
    )
    led = [
        CanonicalLedgerEntry(
            ledger_id="led_dr",
            order_id="ord_prec",
            debit=Decimal("1000.00"),
            credit=Decimal("0.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
            account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
        CanonicalLedgerEntry(
            ledger_id="led_cr",
            order_id="ord_prec",
            debit=Decimal("0.00"),
            credit=Decimal("1000.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
            account=LedgerAccount.ACCOUNTS_RECEIVABLE,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
    ]
    return p, s, led


def test_duplicate_precedence_over_amount_mismatch() -> None:
    """Duplicate settlement payout takes precedence over amount mismatch."""
    engine = DeterministicReconciliationEngine()
    p, s1, led = _setup_base_transaction()
    # s1 has amount delta, s2 is duplicate
    s1_mut = s1.model_copy(update={"settled_amount": Decimal("500.00")})
    s2 = s1.model_copy(update={"settlement_id": "set_prec_2"})

    group = CanonicalTransactionGroup(
        case_id="case_prec_1", order_id="ord_prec", payment=p, settlement=s1_mut, ledger_entries=led
    )
    res = engine.reconcile_group(group, all_matched_settlements=[s1_mut, s2])

    assert res.classification == ExceptionType.DUPLICATE_RECORD


def test_currency_mismatch_precedence_over_amount_mismatch() -> None:
    """Currency conflict takes precedence over monetary delta because conversion is ungrounded."""
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_base_transaction()
    s_mut = s.model_copy(update={"currency": "USD", "settled_amount": Decimal("12.00")})

    group = CanonicalTransactionGroup(
        case_id="case_prec_2", order_id="ord_prec", payment=p, settlement=s_mut, ledger_entries=led
    )
    res = engine.reconcile_group(group)

    assert res.classification == ExceptionType.CURRENCY_MISMATCH


def test_reference_mismatch_precedence_over_date_mismatch() -> None:
    """Broken order identity takes precedence over timing skews."""
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_base_transaction()
    s_preceding = s.model_copy(
        update={"settlement_timestamp": p.payment_timestamp - timedelta(days=5)}
    )
    led_mut = [le.model_copy(update={"order_id": "ord_other"}) for le in led]

    group = CanonicalTransactionGroup(
        case_id="case_prec_3",
        order_id="ord_prec",
        payment=p,
        settlement=s_preceding,
        ledger_entries=led_mut,
    )
    res = engine.reconcile_group(group)

    assert res.classification == ExceptionType.REFERENCE_MISMATCH


def test_date_mismatch_precedence_over_amount_mismatch() -> None:
    """SLA breach/negative timing takes precedence over amount mismatch."""
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_base_transaction()
    s_mut = s.model_copy(
        update={
            "settlement_timestamp": p.payment_timestamp - timedelta(days=1),
            "settled_amount": Decimal("800.00"),
        }
    )

    group = CanonicalTransactionGroup(
        case_id="case_prec_4", order_id="ord_prec", payment=p, settlement=s_mut, ledger_entries=led
    )
    res = engine.reconcile_group(group)

    assert res.classification == ExceptionType.DATE_MISMATCH


def test_fee_discrepancy_precedence_over_generic_amount_mismatch() -> None:
    """When non-standard fee explains the difference exactly, classify as FEE_DISCREPANCY."""
    engine = DeterministicReconciliationEngine()
    p, s, led = _setup_base_transaction()
    # 6% fee schedule explains difference
    s_fee = s.model_copy(
        update={
            "fee": Decimal("60.00"),
            "fee_tax": Decimal("3.60"),
            "settled_amount": Decimal("936.40"),
        }
    )

    group = CanonicalTransactionGroup(
        case_id="case_prec_5", order_id="ord_prec", payment=p, settlement=s_fee, ledger_entries=led
    )
    res = engine.reconcile_group(group)

    assert res.classification == ExceptionType.FEE_DISCREPANCY
