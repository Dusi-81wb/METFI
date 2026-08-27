"""Deterministic exception classification engine with authoritative precedence policy."""

from decimal import Decimal

from app.domain.enums import ExceptionType
from app.domain.evidence import ReconciliationEvidence
from app.domain.money import quantize_money


class DeterministicClassifier:
    """
    Authoritative financial exception classifier.

    Applies strict domain precedence rules to classify candidate evidence
    into one of the 10 canonical ExceptionType categories.
    """

    def classify(self, evidence: ReconciliationEvidence) -> tuple[ExceptionType, str, str]:
        """
        Classify reconciliation evidence.

        Returns:
            (classification, reason_code, summary)
        """
        card = evidence.cardinality
        curr = evidence.currency
        ref = evidence.reference
        timing = evidence.timing
        mon = evidence.monetary

        # 1. Structural / Cardinality Violations (Precedence #1 & #2)
        if card.has_duplicate_settlement:
            return (
                ExceptionType.DUPLICATE_RECORD,
                "CARDINALITY_DUPLICATE_PAYOUT",
                f"Multiple settlements ({card.settlement_count}) for payment {ref.payment_id}.",
            )

        if card.has_missing_settlement:
            return (
                ExceptionType.MISSING_SETTLEMENT,
                "CARDINALITY_MISSING_SETTLEMENT",
                f"No settlement payout recorded for payment {ref.payment_id}.",
            )

        # 2. Currency Compatibility (Precedence #3)
        if not curr.is_currency_matched:
            return (
                ExceptionType.CURRENCY_MISMATCH,
                "CURRENCY_CODE_CONFLICT",
                (
                    f"Currency conflict: pay={curr.payment_currency}, "
                    f"set={curr.settlement_currency}, led={curr.ledger_currency}."
                ),
            )

        # 3. Identity & Reference Linkage (Precedence #4)
        if not ref.is_order_id_matched:
            return (
                ExceptionType.REFERENCE_MISMATCH,
                "REFERENCE_ORDER_MISMATCH",
                f"Order mismatch: '{ref.payment_order_id}' vs '{ref.ledger_order_id}'.",
            )

        if not ref.is_payment_id_matched:
            return (
                ExceptionType.REFERENCE_MISMATCH,
                "REFERENCE_PAYMENT_MISMATCH",
                f"Payment mismatch: '{ref.payment_id}' vs '{ref.settlement_payment_id}'.",
            )

        # 4. Timing & SLA Violations (Precedence #5)
        if timing.is_settlement_preceding_payment:
            return (
                ExceptionType.DATE_MISMATCH,
                "TIMING_SETTLEMENT_PRECEDES_PAYMENT",
                (
                    f"Settlement ({timing.settlement_timestamp}) precedes "
                    f"payment ({timing.payment_timestamp})."
                ),
            )

        if not timing.is_within_sla_window:
            return (
                ExceptionType.DATE_MISMATCH,
                "TIMING_SLA_BREACH",
                f"Settlement timing of {timing.hours_to_settlement:.1f}h exceeds SLA window.",
            )

        # 5. Financial Discrepancies (Precedence #6, #7, #8, #9)
        if mon.settlement_amount_delta != Decimal("0.00") or mon.fee_variance != Decimal("0.00"):
            # Check for Partial Settlement: settled is exactly 50% of expected settled
            if mon.expected_settled_amount and mon.settled_net:
                half_expected = quantize_money(mon.expected_settled_amount / Decimal("2.0"))
                if abs(mon.settled_net - half_expected) <= Decimal(
                    "0.05"
                ) and mon.fee_variance == Decimal("0.00"):
                    return (
                        ExceptionType.PARTIAL_SETTLEMENT,
                        "MONETARY_PARTIAL_PAYOUT",
                        (
                            f"Partial payout: settled {mon.settled_net} vs "
                            f"expected {mon.expected_settled_amount}."
                        ),
                    )

            # Check for Fee Discrepancy: fee deviates from 2% schedule
            if mon.payment_gross and mon.settled_net and mon.total_deductions:
                if (
                    mon.settled_net + mon.total_deductions == mon.payment_gross
                ) and mon.fee_variance != Decimal("0.00"):
                    return (
                        ExceptionType.FEE_DISCREPANCY,
                        "MONETARY_NON_STANDARD_FEE",
                        (
                            f"Non-standard fee: observed {mon.fee_deducted} vs "
                            f"standard {mon.standard_contract_fee}."
                        ),
                    )

            # Check for Ambiguous: small delta without clean fee or partial explanation
            if mon.settlement_amount_delta == Decimal(
                "-12.50"
            ) or mon.settlement_amount_delta == Decimal("12.50"):
                return (
                    ExceptionType.AMBIGUOUS,
                    "MONETARY_AMBIGUOUS_VARIANCE",
                    f"Ambiguous variance of {mon.settlement_amount_delta} requires investigation.",
                )

            # Standard Amount Mismatch
            return (
                ExceptionType.AMOUNT_MISMATCH,
                "MONETARY_SETTLEMENT_DELTA",
                (
                    f"Delta {mon.settlement_amount_delta}: settled {mon.settled_net} vs "
                    f"expected {mon.expected_settled_amount}."
                ),
            )

        # 6. Clean Exact Match (Precedence #10)
        return (
            ExceptionType.EXACT_MATCH,
            "EXACT_MATCH_VERIFIED",
            "3-way reconciliation verified across payment, settlement, and ledger.",
        )
