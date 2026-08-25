"""Unit tests for raw domain schemas and validation."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.raw_models import (
    RawLedgerRecord,
    RawPaymentRecord,
    RawSettlementRecord,
)


def test_raw_payment_schema_valid() -> None:
    """Verify RawPaymentRecord construction with valid fields."""
    payment = RawPaymentRecord(
        payment_id="pay_12345",
        order_id="ord_67890",
        customer_id="cust_101",
        amount=Decimal("1250.00"),
        currency="INR",
        status="SUCCESS",
        payment_timestamp="2026-08-25T10:00:00Z",
        metadata={"method": "upi"},
    )
    assert payment.payment_id == "pay_12345"
    assert payment.amount == Decimal("1250.00")


def test_raw_payment_schema_missing_required() -> None:
    """Verify ValidationError on missing required fields."""
    with pytest.raises(ValidationError):
        RawPaymentRecord(
            payment_id="pay_123",
            order_id="ord_456",
            # Missing customer_id, amount, etc.
        )


def test_raw_settlement_schema_valid() -> None:
    """Verify RawSettlementRecord construction with valid fields."""
    settlement = RawSettlementRecord(
        settlement_id="set_999",
        payment_id="pay_12345",
        settled_amount="1225.00",
        currency="INR",
        settlement_timestamp="2026-08-26T10:00:00Z",
        fee="21.19",
        fee_tax="3.81",
        status="SETTLED",
    )
    assert settlement.settlement_id == "set_999"


def test_raw_ledger_schema_valid() -> None:
    """Verify RawLedgerRecord construction."""
    ledger = RawLedgerRecord(
        ledger_id="led_001",
        order_id="ord_67890",
        debit="1250.00",
        credit="0.00",
        currency="INR",
        entry_timestamp="2026-08-25T10:00:00Z",
        account="PAYMENT_GATEWAY_CLEARING",
        status="POSTED",
    )
    assert ledger.account == "PAYMENT_GATEWAY_CLEARING"
