"""Unit tests for deterministic corruption operators."""

import random
from decimal import Decimal

import pytest

from app.domain.corruption import CORRUPTION_OPERATORS
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.raw_models import RawLedgerRecord, RawPaymentRecord, RawSettlementRecord


@pytest.fixture
def baseline_records() -> tuple[RawPaymentRecord, RawSettlementRecord, list[RawLedgerRecord]]:
    payment = RawPaymentRecord(
        payment_id="pay_test_01",
        order_id="ord_test_01",
        customer_id="cust_001",
        amount=Decimal("1000.00"),
        currency="INR",
        status="SUCCESS",
        payment_timestamp="2026-08-25T10:00:00Z",
    )
    settlement = RawSettlementRecord(
        settlement_id="set_test_01",
        payment_id="pay_test_01",
        settled_amount=Decimal("976.40"),
        currency="INR",
        settlement_timestamp="2026-08-26T10:00:00Z",
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        status="SETTLED",
    )
    ledger_dr = RawLedgerRecord(
        ledger_id="led_test_01_dr",
        order_id="ord_test_01",
        debit=Decimal("1000.00"),
        credit=Decimal("0.00"),
        currency="INR",
        entry_timestamp="2026-08-25T10:00:00Z",
        account="PAYMENT_GATEWAY_CLEARING",
        status="POSTED",
    )
    ledger_cr = RawLedgerRecord(
        ledger_id="led_test_01_cr",
        order_id="ord_test_01",
        debit=Decimal("0.00"),
        credit=Decimal("1000.00"),
        currency="INR",
        entry_timestamp="2026-08-25T10:00:00Z",
        account="ACCOUNTS_RECEIVABLE",
        status="POSTED",
    )
    return payment, settlement, [ledger_dr, ledger_cr]


@pytest.mark.parametrize("exception_type", list(ExceptionType))
def test_all_corruption_operators_deterministic(
    exception_type: ExceptionType,
    baseline_records: tuple[RawPaymentRecord, RawSettlementRecord, list[RawLedgerRecord]],
) -> None:
    """Verify that every corruption operator executes deterministically and annotates fault."""
    payment, settlement, ledger_entries = baseline_records
    operator = CORRUPTION_OPERATORS[exception_type]

    rng1 = random.Random(42)
    bundle1 = operator(payment, settlement, ledger_entries, rng1)

    rng2 = random.Random(42)
    bundle2 = operator(payment, settlement, ledger_entries, rng2)

    assert bundle1.expected_classification == exception_type
    assert bundle1.expected_classification == bundle2.expected_classification
    assert bundle1.fault.exception_type == exception_type
    assert len(bundle1.settlements) == len(bundle2.settlements)
    if bundle1.settlements and bundle2.settlements:
        assert bundle1.settlements[0].settled_amount == bundle2.settlements[0].settled_amount


def test_missing_settlement_operator(
    baseline_records: tuple[RawPaymentRecord, RawSettlementRecord, list[RawLedgerRecord]],
) -> None:
    """Verify missing settlement operator produces empty settlements list."""
    payment, settlement, ledger_entries = baseline_records
    bundle = CORRUPTION_OPERATORS[ExceptionType.MISSING_SETTLEMENT](
        payment, settlement, ledger_entries, random.Random(42)
    )
    assert len(bundle.settlements) == 0
    assert bundle.expected_classification == ExceptionType.MISSING_SETTLEMENT
    assert bundle.expected_policy_outcome == PolicyOutcome.UNRESOLVED


def test_duplicate_record_operator(
    baseline_records: tuple[RawPaymentRecord, RawSettlementRecord, list[RawLedgerRecord]],
) -> None:
    """Verify duplicate operator produces 2 settlement records for same payment."""
    payment, settlement, ledger_entries = baseline_records
    bundle = CORRUPTION_OPERATORS[ExceptionType.DUPLICATE_RECORD](
        payment, settlement, ledger_entries, random.Random(42)
    )
    assert len(bundle.settlements) == 2
    assert bundle.settlements[0].payment_id == bundle.settlements[1].payment_id
    assert bundle.settlements[0].settlement_id != bundle.settlements[1].settlement_id
