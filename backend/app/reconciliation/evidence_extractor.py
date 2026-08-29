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
from app.domain.fee_policy import UNSET_POLICY, FeeTaxPolicy
from app.domain.money import quantize_money
from app.domain.time import hours_between, to_iso_utc


class EvidenceExtractor:
    """Extracts and computes comprehensive financial evidence for a candidate group."""

    def __init__(self, default_policy: FeeTaxPolicy | None = None) -> None:
        self.default_policy = default_policy if default_policy is not None else FeeTaxPolicy()

    def extract_evidence(
        self,
        payment: CanonicalPayment | None,
        settlements: list[CanonicalSettlement],
        ledger_entries: list[CanonicalLedgerEntry],
        policy: FeeTaxPolicy | None | object = UNSET_POLICY,
        is_ambiguous_candidate: bool = False,
        is_cross_customer_rejected: bool = False,
    ) -> ReconciliationEvidence:
        """
        Evaluate candidate group across monetary, currency, timing, reference,
        and cardinality dimensions using active domain policy.
        """
        active_policy = self.default_policy if policy is UNSET_POLICY else policy
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

        standard_fee: Decimal | None = None
        standard_tax: Decimal | None = None
        expected_total_deductions: Decimal | None = None
        expected_settled: Decimal | None = None
        amount_delta = Decimal("0.00")
        fee_variance = Decimal("0.00")
        tax_variance = Decimal("0.00")
        total_deduction_variance = Decimal("0.00")
        is_fee_policy_known = active_policy is not None
        is_fee_compliant = True

        if (
            active_policy is not None
            and isinstance(active_policy, FeeTaxPolicy)
            and gross is not None
        ):
            # Active policy configured: derive deterministic contract expectations
            standard_fee, standard_tax, expected_total_deductions = (
                active_policy.calculate_expected_deductions(gross)
            )
            expected_settled = active_policy.calculate_expected_settled_amount(gross)

            if primary_settlement is not None:
                # Discrepancy between observed settlement and gross minus observed deductions
                expected_with_observed_deductions = quantize_money(
                    gross - primary_settlement.total_deductions
                )
                amount_delta = quantize_money(
                    primary_settlement.settled_amount - expected_with_observed_deductions
                )

                if fee is not None and standard_fee is not None:
                    fee_variance = quantize_money(fee - standard_fee)
                if fee_tax is not None and standard_tax is not None:
                    tax_variance = quantize_money(fee_tax - standard_tax)
                if total_deductions is not None and expected_total_deductions is not None:
                    total_deduction_variance = quantize_money(
                        total_deductions - expected_total_deductions
                    )

                is_fee_compliant = (
                    fee_variance == Decimal("0.00") and tax_variance == Decimal("0.00")
                )
                if fee_variance != Decimal("0.00"):
                    flags.append("FEE_VARIANCE_DETECTED")
                if tax_variance != Decimal("0.00"):
                    flags.append("TAX_VARIANCE_DETECTED")
                if total_deduction_variance != Decimal("0.00"):
                    flags.append("TOTAL_DEDUCTION_VARIANCE_DETECTED")
            elif has_missing_settlement:
                amount_delta = gross

        elif active_policy is None:
            # Fee/tax policy is unknown: DO NOT invent assumptions
            is_fee_policy_known = False
            if gross is not None and primary_settlement is not None:
                expected_settled = quantize_money(gross - primary_settlement.total_deductions)
                amount_delta = quantize_money(
                    primary_settlement.settled_amount - expected_settled
                )
                if primary_settlement.total_deductions > Decimal("0.00"):
                    flags.append("UNKNOWN_FEE_POLICY")
            elif gross is not None and has_missing_settlement:
                expected_settled = gross
                amount_delta = gross

        ledger_debit = sum((le.debit for le in ledger_entries), Decimal("0.00"))
        ledger_credit = sum((le.credit for le in ledger_entries), Decimal("0.00"))
        is_ledger_balanced = (
            (ledger_debit == ledger_credit)
            if ledger_entries
            else (gross is None or gross == Decimal("0.00"))
        )

        if amount_delta != Decimal("0.00"):
            flags.append("AMOUNT_DELTA_NON_ZERO")
        if not is_ledger_balanced and ledger_entries:
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
            expected_total_deductions=expected_total_deductions,
            fee_variance=fee_variance,
            tax_variance=tax_variance,
            total_deduction_variance=total_deduction_variance,
            is_fee_policy_known=is_fee_policy_known,
            is_fee_compliant=is_fee_compliant,
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
        is_cross_customer_matched = not is_cross_customer_rejected

        if not is_pid_match or not is_oid_match:
            flags.append("REFERENCE_MISMATCH")
        if is_cross_customer_rejected:
            flags.append("CROSS_CUSTOMER_MISMATCH")
        if is_ambiguous_candidate:
            flags.append("AMBIGUOUS_CANDIDATES")

        reference = ReferenceEvidence(
            payment_id=p_id,
            settlement_payment_id=s_pid,
            payment_order_id=p_oid,
            ledger_order_id=l_oid,
            customer_id=c_id,
            is_payment_id_matched=is_pid_match,
            is_order_id_matched=is_oid_match,
            candidate_match_count=len(settlements),
            is_cross_customer_matched=is_cross_customer_matched,
            is_ambiguous_candidate=is_ambiguous_candidate,
        )

        return ReconciliationEvidence(
            monetary=monetary,
            currency=currency,
            timing=timing,
            reference=reference,
            cardinality=cardinality,
            flags=flags,
        )
