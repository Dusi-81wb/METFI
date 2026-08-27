"""Structured, immutable evidence models for multi-source financial reconciliation."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MonetaryEvidence(BaseModel):
    """Authoritative monetary comparisons across payment, settlement, and ledger."""

    model_config = ConfigDict(frozen=True)

    payment_gross: Decimal | None = Field(
        default=None, description="Gross authorized payment amount"
    )
    settled_net: Decimal | None = Field(default=None, description="Net settled amount received")
    fee_deducted: Decimal | None = Field(
        default=None, description="Gateway processing fee deducted"
    )
    fee_tax_deducted: Decimal | None = Field(default=None, description="Tax deducted on fee (GST)")
    total_deductions: Decimal | None = Field(default=None, description="Sum of fee and fee tax")
    expected_settled_amount: Decimal | None = Field(
        default=None, description="Calculated expected net: payment_gross - fee - fee_tax"
    )
    settlement_amount_delta: Decimal = Field(
        default=Decimal("0.00"),
        description="Net settlement discrepancy: settled_net - expected_settled",
    )
    standard_contract_fee: Decimal | None = Field(
        default=None, description="Expected standard fee (2% of gross)"
    )
    standard_contract_fee_tax: Decimal | None = Field(
        default=None, description="Expected standard tax (18% of fee)"
    )
    fee_variance: Decimal = Field(
        default=Decimal("0.00"), description="Variance between observed fee and contract fee"
    )
    ledger_debit_total: Decimal = Field(
        default=Decimal("0.00"), description="Sum of debits posted in ledger"
    )
    ledger_credit_total: Decimal = Field(
        default=Decimal("0.00"), description="Sum of credits posted in ledger"
    )
    is_ledger_balanced: bool = Field(
        default=True, description="True if total debits equal total credits"
    )


class CurrencyEvidence(BaseModel):
    """Currency code consistency evidence across sources."""

    model_config = ConfigDict(frozen=True)

    payment_currency: str | None = Field(default=None, description="ISO 4217 code of payment")
    settlement_currency: str | None = Field(default=None, description="ISO 4217 code of settlement")
    ledger_currency: str | None = Field(default=None, description="ISO 4217 code of ledger entries")
    is_currency_matched: bool = Field(
        default=True, description="True if all available source currencies are identical"
    )


class TimingEvidence(BaseModel):
    """Temporal relationship and SLA analysis between authorization, settlement, and posting."""

    model_config = ConfigDict(frozen=True)

    payment_timestamp: str | None = Field(
        default=None, description="Payment authorization timestamp"
    )
    settlement_timestamp: str | None = Field(
        default=None, description="Settlement payout timestamp"
    )
    ledger_timestamp: str | None = Field(default=None, description="Ledger journal timestamp")
    hours_to_settlement: float | None = Field(
        default=None,
        description="Hours elapsed between payment authorization and settlement payout",
    )
    is_settlement_preceding_payment: bool = Field(
        default=False, description="True if settlement timestamp is prior to payment authorization"
    )
    is_within_sla_window: bool = Field(
        default=True,
        description="True if settlement occurred within acceptable SLA (0 to 720 hours)",
    )


class ReferenceEvidence(BaseModel):
    """Entity references and cross-source linkage consistency evidence."""

    model_config = ConfigDict(frozen=True)

    payment_id: str | None = Field(default=None, description="Gateway payment ID")
    settlement_payment_id: str | None = Field(
        default=None, description="Payment ID in settlement record"
    )
    payment_order_id: str | None = Field(default=None, description="Order ID in payment record")
    ledger_order_id: str | None = Field(default=None, description="Order ID in ledger records")
    customer_id: str | None = Field(default=None, description="Customer entity reference")
    is_payment_id_matched: bool = Field(
        default=True, description="True if payment_id matches across payment and settlement"
    )
    is_order_id_matched: bool = Field(
        default=True, description="True if order_id matches across payment and ledger"
    )


class CardinalityEvidence(BaseModel):
    """Source record counts and multiplicity verification."""

    model_config = ConfigDict(frozen=True)

    payment_count: int = Field(default=0, description="Number of matched payment records")
    settlement_count: int = Field(default=0, description="Number of matched settlement records")
    ledger_entry_count: int = Field(default=0, description="Number of matched ledger entries")
    has_missing_payment: bool = Field(default=False, description="Payment record is absent")
    has_missing_settlement: bool = Field(default=False, description="Settlement record is absent")
    has_duplicate_settlement: bool = Field(
        default=False, description="Multiple settlements associated with a single payment"
    )
    has_duplicate_ledger: bool = Field(
        default=False, description="More than standard 2 ledger entries for single order"
    )


class ReconciliationEvidence(BaseModel):
    """Comprehensive, structured evidence bundle proving why a reconciliation decision was made."""

    model_config = ConfigDict(frozen=True)

    monetary: MonetaryEvidence
    currency: CurrencyEvidence
    timing: TimingEvidence
    reference: ReferenceEvidence
    cardinality: CardinalityEvidence
    flags: list[str] = Field(
        default_factory=list,
        description="Machine-readable discrepancy tags detected during evaluation",
    )
