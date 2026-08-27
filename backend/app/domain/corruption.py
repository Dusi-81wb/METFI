"""Deterministic corruption operators for synthetic dataset generation."""

import random
from datetime import timedelta
from decimal import Decimal

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.ground_truth import InjectedFaultDetails
from app.domain.money import quantize_money
from app.domain.raw_models import RawLedgerRecord, RawPaymentRecord, RawSettlementRecord


class CorruptedTransactionBundle:
    """Bundle containing mutated raw records and corresponding ground truth fault details."""

    def __init__(
        self,
        payment: RawPaymentRecord | None,
        settlements: list[RawSettlementRecord],
        ledger_entries: list[RawLedgerRecord],
        fault: InjectedFaultDetails,
        expected_classification: ExceptionType,
        expected_policy_outcome: PolicyOutcome,
        expected_amount_delta: Decimal = Decimal("0.00"),
    ) -> None:
        self.payment = payment
        self.settlements = settlements
        self.ledger_entries = ledger_entries
        self.fault = fault
        self.expected_classification = expected_classification
        self.expected_policy_outcome = expected_policy_outcome
        self.expected_amount_delta = expected_amount_delta


def apply_exact_match(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Produce clean baseline transaction with zero mutations."""
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.EXACT_MATCH,
        description="Clean transaction matching across payment, settlement, and ledger.",
        target_source="none",
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.EXACT_MATCH,
        expected_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        expected_amount_delta=Decimal("0.00"),
    )


def apply_amount_mismatch(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject variance between payment gross and settled amount."""
    delta_options = [Decimal("50.00"), Decimal("100.00"), Decimal("250.00"), Decimal("-150.00")]
    delta = rng.choice(delta_options)
    original_settled = Decimal(str(settlement.settled_amount))
    mutated_settled = quantize_money(original_settled + delta)

    mutated_settlement = settlement.model_copy(update={"settled_amount": mutated_settled})
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.AMOUNT_MISMATCH,
        description=f"Settled amount altered by delta {delta}.",
        target_source="settlement",
        field_mutated="settled_amount",
        original_value=str(original_settled),
        mutated_value=str(mutated_settled),
        delta=delta,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.AMOUNT_MISMATCH,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        expected_amount_delta=delta,
    )


def apply_missing_settlement(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Omit settlement record entirely from dataset."""
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.MISSING_SETTLEMENT,
        description=f"Settlement record {settlement.settlement_id} missing beyond SLA window.",
        target_source="settlement",
        field_mutated="settlement_id",
        original_value=settlement.settlement_id,
        mutated_value=None,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[],  # Empty settlements list
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.MISSING_SETTLEMENT,
        expected_policy_outcome=PolicyOutcome.UNRESOLVED,
        expected_amount_delta=Decimal(str(payment.amount)),
    )


def apply_duplicate_record(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject duplicate settlement record with identical payment reference."""
    import hashlib

    dup_hash = hashlib.sha256(f"dup:{settlement.settlement_id}".encode()).hexdigest()[:12]
    dup_settlement_id = f"set_{dup_hash}"
    duplicate_settlement = settlement.model_copy(
        update={
            "settlement_id": dup_settlement_id,
            "metadata": {**settlement.metadata},
        }
    )
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.DUPLICATE_RECORD,
        description=f"Duplicate payout {dup_settlement_id} for payment {payment.payment_id}.",
        target_source="settlement",
        field_mutated="payment_id",
        original_value=settlement.settlement_id,
        mutated_value=f"{settlement.settlement_id}, {dup_settlement_id}",
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[settlement, duplicate_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.DUPLICATE_RECORD,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        expected_amount_delta=Decimal(str(settlement.settled_amount)),
    )


def apply_date_mismatch(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject settlement timestamp out of SLA or preceding payment timestamp."""
    skew_days = rng.choice([-3, 45, 60])  # Either preceding authorization or 45+ days delayed
    payment_dt = (
        payment.payment_timestamp
        if hasattr(payment.payment_timestamp, "year")
        else str(payment.payment_timestamp)
    )
    from app.domain.time import ensure_utc, to_iso_utc

    p_dt = ensure_utc(payment_dt)
    mutated_dt = to_iso_utc(p_dt + timedelta(days=skew_days))

    mutated_settlement = settlement.model_copy(update={"settlement_timestamp": mutated_dt})
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.DATE_MISMATCH,
        description=f"Settlement timing skew of {skew_days} days relative to payment.",
        target_source="settlement",
        field_mutated="settlement_timestamp",
        original_value=str(settlement.settlement_timestamp),
        mutated_value=mutated_dt,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.DATE_MISMATCH,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
    )


def apply_reference_mismatch(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject character transposition, typo, or truncation in order reference."""
    original_order = payment.order_id
    typo_pos = rng.randint(4, len(original_order) - 1)
    chars = list(original_order)
    chars[typo_pos] = "X" if chars[typo_pos] != "X" else "Y"
    mutated_order = "".join(chars)

    mutated_ledger = [le.model_copy(update={"order_id": mutated_order}) for le in ledger_entries]
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.REFERENCE_MISMATCH,
        description=(
            f"Order reference mutated in ledger from '{original_order}' to '{mutated_order}'."
        ),
        target_source="ledger",
        field_mutated="order_id",
        original_value=original_order,
        mutated_value=mutated_order,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[settlement],
        ledger_entries=mutated_ledger,
        fault=fault,
        expected_classification=ExceptionType.REFERENCE_MISMATCH,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
    )


def apply_partial_settlement(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject partial settlement (e.g. 50% settled funds)."""
    original_settled = Decimal(str(settlement.settled_amount))
    partial_settled = quantize_money(original_settled / Decimal("2.0"))
    delta = original_settled - partial_settled

    mutated_settlement = settlement.model_copy(update={"settled_amount": partial_settled})
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.PARTIAL_SETTLEMENT,
        description=f"Partial settlement payout: settled {partial_settled} of {original_settled}.",
        target_source="settlement",
        field_mutated="settled_amount",
        original_value=str(original_settled),
        mutated_value=str(partial_settled),
        delta=delta,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.PARTIAL_SETTLEMENT,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        expected_amount_delta=delta,
    )


def apply_fee_discrepancy(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject fee deduction calculation error (e.g. 6% fee schedule instead of standard 2%)."""
    gross = Decimal(str(payment.amount))
    abnormal_fee = quantize_money(gross * Decimal("0.06"))
    original_fee = Decimal(str(settlement.fee))
    fee_diff = abnormal_fee - original_fee

    original_settled = Decimal(str(settlement.settled_amount))
    mutated_settled = quantize_money(original_settled - fee_diff)

    mutated_settlement = settlement.model_copy(
        update={"fee": abnormal_fee, "settled_amount": mutated_settled}
    )
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.FEE_DISCREPANCY,
        description=f"Abnormal processing fee {abnormal_fee} deducted (expected {original_fee}).",
        target_source="settlement",
        field_mutated="fee",
        original_value=str(original_fee),
        mutated_value=str(abnormal_fee),
        delta=fee_diff,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.FEE_DISCREPANCY,
        expected_policy_outcome=PolicyOutcome.REVIEW_REQUIRED,
        expected_amount_delta=fee_diff,
    )


def apply_currency_mismatch(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject currency code mismatch between payment and settlement."""
    alt_currency = rng.choice(["USD", "EUR", "GBP"])
    mutated_settlement = settlement.model_copy(update={"currency": alt_currency})
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.CURRENCY_MISMATCH,
        description=f"Settlement currency '{alt_currency}' conflicts with '{payment.currency}'.",
        target_source="settlement",
        field_mutated="currency",
        original_value=payment.currency,
        mutated_value=alt_currency,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.CURRENCY_MISMATCH,
        expected_policy_outcome=PolicyOutcome.UNRESOLVED,
    )


def apply_ambiguous(
    payment: RawPaymentRecord,
    settlement: RawSettlementRecord,
    ledger_entries: list[RawLedgerRecord],
    rng: random.Random,
) -> CorruptedTransactionBundle:
    """Inject multi-factor ambiguous discrepancy without semantic label leakage."""
    delta = Decimal("12.50")
    original_settled = Decimal(str(settlement.settled_amount))
    mutated_settled = quantize_money(original_settled - delta)
    mutated_settlement = settlement.model_copy(
        update={
            "settled_amount": mutated_settled,
            "metadata": {**settlement.metadata},
        }
    )
    fault = InjectedFaultDetails(
        exception_type=ExceptionType.AMBIGUOUS,
        description="Complex multi-factor discrepancy requiring deep evidence reasoning.",
        target_source="cross",
        field_mutated="settled_amount",
        original_value=str(original_settled),
        mutated_value=str(mutated_settled),
        delta=delta,
    )
    return CorruptedTransactionBundle(
        payment=payment,
        settlements=[mutated_settlement],
        ledger_entries=ledger_entries,
        fault=fault,
        expected_classification=ExceptionType.AMBIGUOUS,
        expected_policy_outcome=PolicyOutcome.UNRESOLVED,
        expected_amount_delta=delta,
    )


CORRUPTION_OPERATORS = {
    ExceptionType.EXACT_MATCH: apply_exact_match,
    ExceptionType.AMOUNT_MISMATCH: apply_amount_mismatch,
    ExceptionType.MISSING_SETTLEMENT: apply_missing_settlement,
    ExceptionType.DUPLICATE_RECORD: apply_duplicate_record,
    ExceptionType.DATE_MISMATCH: apply_date_mismatch,
    ExceptionType.REFERENCE_MISMATCH: apply_reference_mismatch,
    ExceptionType.PARTIAL_SETTLEMENT: apply_partial_settlement,
    ExceptionType.FEE_DISCREPANCY: apply_fee_discrepancy,
    ExceptionType.CURRENCY_MISMATCH: apply_currency_mismatch,
    ExceptionType.AMBIGUOUS: apply_ambiguous,
}
