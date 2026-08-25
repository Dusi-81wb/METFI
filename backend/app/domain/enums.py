"""Domain enums and exception taxonomy for METFI."""

from enum import StrEnum


class PaymentStatus(StrEnum):
    """Status of payment transactions in payment gateway source."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"


class SettlementStatus(StrEnum):
    """Status of settlement payouts in acquirer/bank source."""

    SETTLED = "SETTLED"
    HOLD = "HOLD"
    FAILED = "FAILED"


class LedgerAccount(StrEnum):
    """Standard merchant general ledger accounts."""

    ACCOUNTS_RECEIVABLE = "ACCOUNTS_RECEIVABLE"
    PAYMENT_GATEWAY_CLEARING = "PAYMENT_GATEWAY_CLEARING"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    PROCESSING_FEE_EXPENSE = "PROCESSING_FEE_EXPENSE"
    SALES_REVENUE = "SALES_REVENUE"
    REFUND_EXPENSE = "REFUND_EXPENSE"


class LedgerStatus(StrEnum):
    """Status of general ledger journal postings."""

    POSTED = "POSTED"
    DRAFT = "DRAFT"
    REVERSED = "REVERSED"


class ExceptionType(StrEnum):
    """Canonical 10-class reconciliation exception taxonomy (Master Spec §7)."""

    EXACT_MATCH = "EXACT_MATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    DATE_MISMATCH = "DATE_MISMATCH"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"
    FEE_DISCREPANCY = "FEE_DISCREPANCY"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"


class PolicyOutcome(StrEnum):
    """Deterministic policy authorization decision outcomes (Master Spec §11)."""

    AUTO_RECONCILE = "AUTO_RECONCILE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNRESOLVED = "UNRESOLVED"
