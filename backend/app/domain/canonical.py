"""Canonical normalized data models for METFI financial reconciliation."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    SettlementStatus,
)


class CanonicalPayment(BaseModel):
    """Canonical, validated payment authorization representation."""

    model_config = ConfigDict(frozen=True)

    payment_id: str = Field(description="Normalized payment identifier")
    order_id: str = Field(description="Normalized merchant order reference")
    customer_id: str = Field(description="Normalized customer identifier")
    amount: Decimal = Field(description="Gross payment amount (exact 2-decimal)")
    currency: str = Field(description="ISO 4217 uppercase currency code")
    status: PaymentStatus = Field(description="Normalized payment status")
    payment_timestamp: datetime = Field(description="UTC timezone-aware authorization timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class CanonicalSettlement(BaseModel):
    """Canonical, validated bank/acquirer settlement representation."""

    model_config = ConfigDict(frozen=True)

    settlement_id: str = Field(description="Normalized settlement identifier")
    payment_id: str = Field(description="Normalized payment identifier")
    settled_amount: Decimal = Field(description="Net funds settled (exact 2-decimal)")
    currency: str = Field(description="ISO 4217 uppercase currency code")
    settlement_timestamp: datetime = Field(description="UTC timezone-aware settlement timestamp")
    fee: Decimal = Field(description="Normalized gateway processing fee")
    fee_tax: Decimal = Field(description="Normalized fee tax (e.g. GST)")
    status: SettlementStatus = Field(description="Normalized settlement status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")

    @property
    def total_deductions(self) -> Decimal:
        """Total fees and taxes deducted during settlement."""
        return self.fee + self.fee_tax

    @property
    def gross_expected_amount(self) -> Decimal:
        """Computed gross amount before fee deductions."""
        return self.settled_amount + self.total_deductions


class CanonicalLedgerEntry(BaseModel):
    """Canonical, validated general ledger journal entry representation."""

    model_config = ConfigDict(frozen=True)

    ledger_id: str = Field(description="Normalized ledger journal identifier")
    order_id: str = Field(description="Normalized merchant order reference")
    debit: Decimal = Field(description="Debit monetary amount")
    credit: Decimal = Field(description="Credit monetary amount")
    currency: str = Field(description="ISO 4217 uppercase currency code")
    entry_timestamp: datetime = Field(description="UTC timezone-aware posting timestamp")
    account: LedgerAccount = Field(description="Target ledger account")
    status: LedgerStatus = Field(description="Normalized ledger posting status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")

    @property
    def net_balance_impact(self) -> Decimal:
        """Net monetary balance impact (debit - credit)."""
        return self.debit - self.credit


class CanonicalTransactionGroup(BaseModel):
    """Logical grouping of tri-source candidate records for reconciliation."""

    case_id: str = Field(description="Unique reconciliation case identifier")
    order_id: str = Field(description="Merchant order reference tying records together")
    payment: CanonicalPayment | None = Field(default=None, description="Matched canonical payment")
    settlement: CanonicalSettlement | None = Field(
        default=None, description="Matched canonical settlement"
    )
    ledger_entries: list[CanonicalLedgerEntry] = Field(
        default_factory=list, description="Associated canonical ledger entries"
    )
