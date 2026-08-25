"""Unit tests for deterministic normalization engine."""

from decimal import Decimal

import pytest

from app.domain.enums import (
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    SettlementStatus,
)
from app.domain.normalizer import (
    NormalizationError,
    normalize_ledger,
    normalize_payment,
    normalize_settlement,
)


def test_normalize_payment_success() -> None:
    """Verify normalizing raw payment dictionary into CanonicalPayment."""
    raw = {
        "payment_id": "  pay_001  ",
        "order_id": "ord_001",
        "customer_id": "cust_101",
        "amount": "1250.50",
        "currency": " inr ",
        "status": "success",
        "payment_timestamp": "2026-08-25T10:00:00Z",
    }
    canonical = normalize_payment(raw)
    assert canonical.payment_id == "pay_001"
    assert canonical.amount == Decimal("1250.50")
    assert canonical.currency == "INR"
    assert canonical.status == PaymentStatus.SUCCESS


def test_normalize_payment_invalid_amount() -> None:
    """Verify NormalizationError on negative amount."""
    raw = {
        "payment_id": "pay_001",
        "order_id": "ord_001",
        "customer_id": "cust_101",
        "amount": "-50.00",
        "currency": "INR",
        "status": "SUCCESS",
        "payment_timestamp": "2026-08-25T10:00:00Z",
    }
    with pytest.raises(NormalizationError, match="amount normalization failed"):
        normalize_payment(raw)


def test_normalize_settlement_success() -> None:
    """Verify normalizing raw settlement into CanonicalSettlement."""
    raw = {
        "settlement_id": "set_100",
        "payment_id": "pay_001",
        "settled_amount": "1225.00",
        "currency": "inr",
        "settlement_timestamp": "2026-08-26T10:00:00Z",
        "fee": "21.19",
        "fee_tax": "3.81",
        "status": "SETTLED",
    }
    canonical = normalize_settlement(raw)
    assert canonical.settled_amount == Decimal("1225.00")
    assert canonical.fee == Decimal("21.19")
    assert canonical.fee_tax == Decimal("3.81")
    assert canonical.total_deductions == Decimal("25.00")
    assert canonical.gross_expected_amount == Decimal("1250.00")
    assert canonical.status == SettlementStatus.SETTLED


def test_normalize_ledger_success() -> None:
    """Verify normalizing raw ledger entry into CanonicalLedgerEntry."""
    raw = {
        "ledger_id": "led_01",
        "order_id": "ord_001",
        "debit": "1250.00",
        "credit": "0.00",
        "currency": "INR",
        "entry_timestamp": "2026-08-25T10:00:00Z",
        "account": "PAYMENT_GATEWAY_CLEARING",
        "status": "posted",
    }
    canonical = normalize_ledger(raw)
    assert canonical.debit == Decimal("1250.00")
    assert canonical.credit == Decimal("0.00")
    assert canonical.net_balance_impact == Decimal("1250.00")
    assert canonical.account == LedgerAccount.PAYMENT_GATEWAY_CLEARING
    assert canonical.status == LedgerStatus.POSTED
