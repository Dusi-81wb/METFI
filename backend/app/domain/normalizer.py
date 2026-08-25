"""Deterministic normalization engine transforming raw ingests to canonical entities."""

from typing import Any

from pydantic import ValidationError

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.enums import (
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    SettlementStatus,
)
from app.domain.money import (
    MonetaryValidationError,
    normalize_currency,
    validate_money_amount,
)
from app.domain.raw_models import (
    RawLedgerRecord,
    RawPaymentRecord,
    RawSettlementRecord,
)
from app.domain.time import (
    TimestampValidationError,
    ensure_utc,
)


class NormalizationError(ValueError):
    """Raised when raw financial records fail normalization or validation rules."""

    def __init__(self, message: str, source_record: Any = None, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.source_record = source_record
        self.field = field


def _clean_identifier(val: Any, field_name: str) -> str:
    """Trim whitespace and validate that identifier is non-empty string."""
    if not isinstance(val, str):
        raise NormalizationError(
            f"{field_name} must be a string, got {type(val).__name__}", field=field_name
        )
    cleaned = val.strip()
    if not cleaned:
        raise NormalizationError(f"{field_name} cannot be blank or whitespace.", field=field_name)
    return cleaned


def normalize_payment(raw: RawPaymentRecord | dict[str, Any]) -> CanonicalPayment:
    """
    Deterministically normalize a raw payment record into CanonicalPayment.

    Validates:
    - ID formats (non-empty trimmed strings)
    - Non-negative Decimal monetary amount (2-decimal quantization)
    - Uppercase ISO 4217 currency
    - Timezone-aware UTC ISO timestamp
    - Valid PaymentStatus enum
    """
    if isinstance(raw, dict):
        try:
            raw_model = RawPaymentRecord(**raw)
        except ValidationError as e:
            raise NormalizationError(
                f"Raw payment schema validation failed: {e}", source_record=raw
            ) from e
    else:
        raw_model = raw

    payment_id = _clean_identifier(raw_model.payment_id, "payment_id")
    order_id = _clean_identifier(raw_model.order_id, "order_id")
    customer_id = _clean_identifier(raw_model.customer_id, "customer_id")

    try:
        amount = validate_money_amount(raw_model.amount, allow_negative=False, field_name="amount")
    except MonetaryValidationError as e:
        raise NormalizationError(f"Payment amount normalization failed: {e}", field="amount") from e

    try:
        currency = normalize_currency(raw_model.currency)
    except MonetaryValidationError as e:
        raise NormalizationError(
            f"Payment currency normalization failed: {e}", field="currency"
        ) from e

    try:
        payment_ts = ensure_utc(raw_model.payment_timestamp)
    except TimestampValidationError as e:
        raise NormalizationError(
            f"Payment timestamp normalization failed: {e}", field="payment_timestamp"
        ) from e

    try:
        status_clean = str(raw_model.status).strip().upper()
        status = PaymentStatus(status_clean)
    except ValueError as e:
        allowed = [s.value for s in PaymentStatus]
        raise NormalizationError(
            f"Invalid payment status '{raw_model.status}'. Allowed: {allowed}",
            field="status",
        ) from e

    return CanonicalPayment(
        payment_id=payment_id,
        order_id=order_id,
        customer_id=customer_id,
        amount=amount,
        currency=currency,
        status=status,
        payment_timestamp=payment_ts,
        metadata=dict(raw_model.metadata),
    )


def normalize_settlement(raw: RawSettlementRecord | dict[str, Any]) -> CanonicalSettlement:
    """
    Deterministically normalize a raw settlement record into CanonicalSettlement.

    Validates:
    - Settlement & payment identifiers
    - Decimal settled amount, fee, fee_tax
    - Uppercase ISO 4217 currency
    - Timezone-aware UTC ISO timestamp
    - Valid SettlementStatus enum
    """
    if isinstance(raw, dict):
        try:
            raw_model = RawSettlementRecord(**raw)
        except ValidationError as e:
            raise NormalizationError(
                f"Raw settlement schema validation failed: {e}", source_record=raw
            ) from e
    else:
        raw_model = raw

    settlement_id = _clean_identifier(raw_model.settlement_id, "settlement_id")
    payment_id = _clean_identifier(raw_model.payment_id, "payment_id")

    try:
        settled_amount = validate_money_amount(
            raw_model.settled_amount, allow_negative=False, field_name="settled_amount"
        )
        fee = validate_money_amount(raw_model.fee, allow_negative=False, field_name="fee")
        fee_tax = validate_money_amount(
            raw_model.fee_tax, allow_negative=False, field_name="fee_tax"
        )
    except MonetaryValidationError as e:
        raise NormalizationError(f"Settlement monetary normalization failed: {e}") from e

    try:
        currency = normalize_currency(raw_model.currency)
    except MonetaryValidationError as e:
        raise NormalizationError(
            f"Settlement currency normalization failed: {e}", field="currency"
        ) from e

    try:
        settlement_ts = ensure_utc(raw_model.settlement_timestamp)
    except TimestampValidationError as e:
        raise NormalizationError(
            f"Settlement timestamp normalization failed: {e}", field="settlement_timestamp"
        ) from e

    try:
        status_clean = str(raw_model.status).strip().upper()
        status = SettlementStatus(status_clean)
    except ValueError as e:
        allowed = [s.value for s in SettlementStatus]
        raise NormalizationError(
            f"Invalid settlement status '{raw_model.status}'. Allowed: {allowed}",
            field="status",
        ) from e

    return CanonicalSettlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        settled_amount=settled_amount,
        currency=currency,
        settlement_timestamp=settlement_ts,
        fee=fee,
        fee_tax=fee_tax,
        status=status,
        metadata=dict(raw_model.metadata),
    )


def normalize_ledger(raw: RawLedgerRecord | dict[str, Any]) -> CanonicalLedgerEntry:
    """
    Deterministically normalize a raw general ledger entry into CanonicalLedgerEntry.

    Validates:
    - Ledger identifier & order reference
    - Non-negative debit and credit values (exact Decimal)
    - Target ledger account and posting status
    - Timezone-aware UTC timestamp
    """
    if isinstance(raw, dict):
        try:
            raw_model = RawLedgerRecord(**raw)
        except ValidationError as e:
            raise NormalizationError(
                f"Raw ledger schema validation failed: {e}", source_record=raw
            ) from e
    else:
        raw_model = raw

    ledger_id = _clean_identifier(raw_model.ledger_id, "ledger_id")
    order_id = _clean_identifier(raw_model.order_id, "order_id")

    try:
        debit = validate_money_amount(raw_model.debit, allow_negative=False, field_name="debit")
        credit = validate_money_amount(raw_model.credit, allow_negative=False, field_name="credit")
    except MonetaryValidationError as e:
        raise NormalizationError(f"Ledger monetary normalization failed: {e}") from e

    # A single journal line cannot have both zero debit and zero credit unless draft
    if debit == 0 and credit == 0:
        raise NormalizationError("Ledger entry must have non-zero debit or credit amount.")

    try:
        currency = normalize_currency(raw_model.currency)
    except MonetaryValidationError as e:
        raise NormalizationError(
            f"Ledger currency normalization failed: {e}", field="currency"
        ) from e

    try:
        entry_ts = ensure_utc(raw_model.entry_timestamp)
    except TimestampValidationError as e:
        raise NormalizationError(
            f"Ledger timestamp normalization failed: {e}", field="entry_timestamp"
        ) from e

    try:
        account_clean = str(raw_model.account).strip().upper()
        account = LedgerAccount(account_clean)
    except ValueError as e:
        allowed = [a.value for a in LedgerAccount]
        raise NormalizationError(
            f"Invalid ledger account '{raw_model.account}'. Allowed: {allowed}",
            field="account",
        ) from e

    try:
        status_clean = str(raw_model.status).strip().upper()
        status = LedgerStatus(status_clean)
    except ValueError as e:
        allowed = [s.value for s in LedgerStatus]
        raise NormalizationError(
            f"Invalid ledger status '{raw_model.status}'. Allowed: {allowed}",
            field="status",
        ) from e

    return CanonicalLedgerEntry(
        ledger_id=ledger_id,
        order_id=order_id,
        debit=debit,
        credit=credit,
        currency=currency,
        entry_timestamp=entry_ts,
        account=account,
        status=status,
        metadata=dict(raw_model.metadata),
    )
