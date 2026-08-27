"""Deterministic evidence extractor evaluating multi-source reconciliation candidate groups."""

from decimal import Decimal

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.money import quantize_money
from app.domain.time import hours_between, to_iso_utc


class EvidenceExtractor:
    """Extracts and computes comprehensive financial evidence for a candidate group."""

    def extract_evidence(
        self,
        payment: CanonicalPayment | None,
        settlements: list[CanonicalSettlement],
        ledger_entries: list[CanonicalLedgerEntry],
    ) -> ReconciliationEvidence:
        """
        Evaluate candidate group across monetary, currency, timing, reference,
        and cardinality dimensions.
        """
        flags: list[str] = []
        primary_settlement = settlements[0] if settlements else None

        # 1. Cardinality Evaluation
        payment_count = 1 if payment else 0
        settlement_count = len(settlements)
        ledger_count = len(ledger_entries)

        has_missing_payment = payment is None
        has_missing_settlement = settlement_count == 0
        has_duplicate_settlement = settlement_count > 1
        has_duplicate_ledger = ledger_count > 2

        if has_missing_settlement:
            flags.append("MISSING_SETTLEMENT")
        if has_duplicate_settlement:
            flags.append("DUPLICATE_SETTLEMENT")

        cardinality = CardinalityEvidence(
            payment_count=payment_count,
            settlement_count=settlement_count,
            ledger_entry_count=ledger_count,
            has_missing_payment=has_missing_payment,
            has_missing_settlement=has_missing_settlement,
            has_duplicate_settlement=has_duplicate_settlement,
            has_duplicate_ledger=has_duplicate_ledger,
        )

        # 2. Monetary Evaluation
        gross = payment.amount if payment else None
        settled_net = primary_settlement.settled_amount if primary_settlement else None
        fee = primary_settlement.fee if primary_settlement else None
        fee_tax = primary_settlement.fee_tax if primary_settlement else None
        total_deductions = primary_settlement.total_deductions if primary_settlement else None

        standard_fee = quantize_money(gross * Decimal("0.02")) if gross else None
        standard_tax = quantize_money(standard_fee * Decimal("0.18")) if standard_fee else None

        expected_settled: Decimal | None = None
        amount_delta = Decimal("0.00")
        fee_variance = Decimal("0.00")

        if gross is not None and primary_settlement is not None:
            expected_settled = quantize_money(
                gross - (primary_settlement.fee + primary_settlement.fee_tax)
            )
            amount_delta = quantize_money(primary_settlement.settled_amount - expected_settled)
            if standard_fee is not None:
                fee_variance = quantize_money(primary_settlement.fee - standard_fee)
        elif gross is not None and has_missing_settlement:
            amount_delta = gross

        ledger_debit = sum((le.debit for le in ledger_entries), Decimal("0.00"))
        ledger_credit = sum((le.credit for le in ledger_entries), Decimal("0.00"))
        is_ledger_balanced = ledger_debit == ledger_credit

        if amount_delta != Decimal("0.00"):
            flags.append("AMOUNT_DELTA_NON_ZERO")
        if fee_variance != Decimal("0.00"):
            flags.append("FEE_VARIANCE_DETECTED")
        if not is_ledger_balanced:
            flags.append("LEDGER_IMBALANCE")

        monetary = MonetaryEvidence(
            payment_gross=gross,
            settled_net=settled_net,
            fee_deducted=fee,
            fee_tax_deducted=fee_tax,
            total_deductions=total_deductions,
            expected_settled_amount=expected_settled,
            settlement_amount_delta=amount_delta,
            standard_contract_fee=standard_fee,
            standard_contract_fee_tax=standard_tax,
            fee_variance=fee_variance,
            ledger_debit_total=ledger_debit,
            ledger_credit_total=ledger_credit,
            is_ledger_balanced=is_ledger_balanced,
        )

        # 3. Currency Evaluation
        p_curr = payment.currency if payment else None
        s_curr = primary_settlement.currency if primary_settlement else None
        l_curr = ledger_entries[0].currency if ledger_entries else None

        present_currencies = {c for c in [p_curr, s_curr, l_curr] if c is not None}
        is_currency_matched = len(present_currencies) <= 1

        if not is_currency_matched:
            flags.append("CURRENCY_MISMATCH")

        currency = CurrencyEvidence(
            payment_currency=p_curr,
            settlement_currency=s_curr,
            ledger_currency=l_curr,
            is_currency_matched=is_currency_matched,
        )

        # 4. Timing Evaluation
        p_ts = to_iso_utc(payment.payment_timestamp) if payment else None
        s_ts = to_iso_utc(primary_settlement.settlement_timestamp) if primary_settlement else None
        l_ts = to_iso_utc(ledger_entries[0].entry_timestamp) if ledger_entries else None

        hours_to_set: float | None = None
        is_preceding = False
        within_sla = True

        if payment and primary_settlement:
            hours_to_set = hours_between(
                payment.payment_timestamp, primary_settlement.settlement_timestamp
            )
            if hours_to_set < 0.0:
                is_preceding = True
                flags.append("SETTLEMENT_PRECEDES_PAYMENT")
            if hours_to_set < 0.0 or hours_to_set > 720.0:  # 30-day SLA window (720 hours)
                within_sla = False
                flags.append("SLA_BREACH")

        timing = TimingEvidence(
            payment_timestamp=p_ts,
            settlement_timestamp=s_ts,
            ledger_timestamp=l_ts,
            hours_to_settlement=hours_to_set,
            is_settlement_preceding_payment=is_preceding,
            is_within_sla_window=within_sla,
        )

        # 5. Reference Evaluation
        p_id = payment.payment_id if payment else None
        s_pid = primary_settlement.payment_id if primary_settlement else None
        p_oid = payment.order_id if payment else None
        l_oid = ledger_entries[0].order_id if ledger_entries else None
        c_id = payment.customer_id if payment else None

        is_pid_match = (p_id == s_pid) if (payment and primary_settlement) else True
        is_oid_match = (p_oid == l_oid) if (payment and ledger_entries) else True

        if not is_pid_match or not is_oid_match:
            flags.append("REFERENCE_MISMATCH")

        reference = ReferenceEvidence(
            payment_id=p_id,
            settlement_payment_id=s_pid,
            payment_order_id=p_oid,
            ledger_order_id=l_oid,
            customer_id=c_id,
            is_payment_id_matched=is_pid_match,
            is_order_id_matched=is_oid_match,
        )

        return ReconciliationEvidence(
            monetary=monetary,
            currency=currency,
            timing=timing,
            reference=reference,
            cardinality=cardinality,
            flags=flags,
        )
