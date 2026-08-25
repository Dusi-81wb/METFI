"""Raw-source ingest schemas for Payments, Settlements, and Ledger records."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawPaymentRecord(BaseModel):
    """Raw transaction ingest model from payment gateway source."""

    model_config = ConfigDict(extra="ignore")

    payment_id: str = Field(description="Unique payment transaction identifier")
    order_id: str = Field(description="Associated merchant order reference")
    customer_id: str = Field(description="Customer identifier")
    amount: Decimal | str | int = Field(description="Gross payment amount")
    currency: str = Field(description="3-letter currency code")
    status: str = Field(description="Payment status: SUCCESS, FAILED, PENDING, REFUNDED")
    payment_timestamp: str | datetime = Field(description="Payment authorization timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom payment metadata")


class RawSettlementRecord(BaseModel):
    """Raw settlement payout model from bank/acquirer source."""

    model_config = ConfigDict(extra="ignore")

    settlement_id: str = Field(description="Unique settlement payout identifier")
    payment_id: str = Field(description="Associated payment identifier")
    settled_amount: Decimal | str | int = Field(description="Net settled funds")
    currency: str = Field(description="Settlement currency code")
    settlement_timestamp: str | datetime = Field(description="Settlement payout timestamp")
    fee: Decimal | str | int = Field(description="Gateway/acquirer processing fee")
    fee_tax: Decimal | str | int = Field(description="Tax levied on fee (e.g. GST)")
    status: str = Field(description="Settlement status: SETTLED, HOLD, FAILED")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Acquirer metadata")


class RawLedgerRecord(BaseModel):
    """Raw journal entry model from merchant general ledger / ERP."""

    model_config = ConfigDict(extra="ignore")

    ledger_id: str = Field(description="Unique ledger journal entry identifier")
    order_id: str = Field(description="Associated merchant order reference")
    debit: Decimal | str | int = Field(description="Debit amount in exact decimal")
    credit: Decimal | str | int = Field(description="Credit amount in exact decimal")
    currency: str = Field(description="Ledger currency code")
    entry_timestamp: str | datetime = Field(description="Ledger journal posting timestamp")
    account: str = Field(description="Target ledger account")
    status: str = Field(description="Posting status: POSTED, DRAFT, REVERSED")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Accounting voucher metadata"
    )
