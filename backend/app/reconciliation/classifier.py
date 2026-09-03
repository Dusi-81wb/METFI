"""Deterministic exception classification engine with authoritative financial precedence."""

from decimal import Decimal

from app.domain.enums import ExceptionType
from app.domain.evidence import ReconciliationEvidence
from app.services.rule_service import RuleService


class DeterministicClassifier:
    """
    Authoritative financial exception classifier.

    Applies strict domain precedence rules to classify candidate evidence
    into one of the 10 canonical ExceptionType categories without generator-specific heuristics.
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
        flags = set(evidence.flags)

        # 1. Structural / Cardinality Violations (Precedence #1 & #2)
        if card.has_duplicate_settlement:
            return (
                ExceptionType.DUPLICATE_RECORD,
                "CARDINALITY_DUPLICATE_PAYOUT",
                (
                    f"Multiple settlements ({card.settlement_count}) "
                    f"recorded for payment {ref.payment_id}."
                ),
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
                    f"Currency conflict across feeds: pay={curr.payment_currency}, "
                    f"set={curr.settlement_currency}, led={curr.ledger_currency}."
                ),
            )

        # 3. Purview Custom Classification Rule Evaluation
        # Check user-configured custom classification rules if enabled
        custom_rule_result = RuleService.get_instance().evaluate_custom_classification(evidence)
        if custom_rule_result is not None:
            c_rule, c_target_cls, c_reason = custom_rule_result
            return (
                c_target_cls,
                c_reason,
                f"Custom Rule '{c_rule.name}' applied: {c_rule.description}",
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

        # 5. Evidence Ambiguity / Structural Linkage Conflict (Precedence #6)
        if ref.is_ambiguous_candidate or "AMBIGUOUS_CANDIDATES" in flags:
            return (
                ExceptionType.AMBIGUOUS,
                "AMBIGUOUS_CANDIDATE_TIE",
                "Multiple equally plausible candidate matches identified with unresolved tie.",
            )

        if not ref.is_cross_customer_matched or "CROSS_CUSTOMER_MISMATCH" in flags:
            return (
                ExceptionType.AMBIGUOUS,
                "CROSS_CUSTOMER_CONFLICT",
                "Conflicting customer identities detected across candidate records.",
            )

        # 6. Fee and Tax Pricing Discrepancies (Precedence #7)
        # Gross equals Settled plus Total Deductions, but rates deviate from policy
        if (
            mon.is_fee_policy_known
            and mon.payment_gross is not None
            and mon.settled_net is not None
            and mon.total_deductions is not None
        ):
            is_gross_balanced = mon.settled_net + mon.total_deductions == mon.payment_gross
            if is_gross_balanced and not mon.is_fee_compliant:
                if mon.tax_variance != Decimal("0.00") and mon.fee_variance == Decimal("0.00"):
                    return (
                        ExceptionType.FEE_DISCREPANCY,
                        "TAX_VARIANCE_DETECTED",
                        (
                            f"Non-standard tax on fee: observed {mon.fee_tax_deducted} vs "
                            f"policy {mon.standard_contract_fee_tax} "
                            f"(tax variance {mon.tax_variance})."
                        ),
                    )
                if mon.fee_variance != Decimal("0.00") and mon.tax_variance == Decimal("0.00"):
                    return (
                        ExceptionType.FEE_DISCREPANCY,
                        "FEE_VARIANCE_DETECTED",
                        (
                            f"Non-standard gateway fee: observed {mon.fee_deducted} vs "
                            f"policy {mon.standard_contract_fee} "
                            f"(fee variance {mon.fee_variance})."
                        ),
                    )
                return (
                    ExceptionType.FEE_DISCREPANCY,
                    "FEE_TAX_VARIANCE_DETECTED",
                    (
                        f"Non-standard fee and tax schedule: fee variance {mon.fee_variance}, "
                        f"tax variance {mon.tax_variance}."
                    ),
                )

        # 7. Partial Settlement (Precedence #8)
        # Fractional principal disbursement (< 90% of expected collectible net amount)
        if (
            mon.expected_settled_amount is not None
            and mon.settled_net is not None
            and mon.payment_gross is not None
        ):
            if (
                Decimal("0.00") < mon.settled_net < mon.expected_settled_amount
                and mon.settlement_amount_delta != Decimal("0.00")
            ):
                ratio = mon.settled_net / mon.expected_settled_amount
                # Fractional principal payout (up to 90% of expected net funds)
                if ratio <= Decimal("0.90"):
                    shortfall = mon.expected_settled_amount - mon.settled_net
                    return (
                        ExceptionType.PARTIAL_SETTLEMENT,
                        "MONETARY_PARTIAL_PAYOUT",
                        (
                            f"Partial payout ({ratio * 100:.1f}%): settled {mon.settled_net} "
                            f"of expected {mon.expected_settled_amount} (shortfall {shortfall})."
                        ),
                    )

        # 8. Unexplained Capital Discrepancy / Amount Mismatch (Precedence #9)
        if mon.settlement_amount_delta != Decimal("0.00"):
            return (
                ExceptionType.AMOUNT_MISMATCH,
                "MONETARY_SETTLEMENT_DELTA",
                (
                    f"Settlement delta of {mon.settlement_amount_delta}: "
                    f"observed {mon.settled_net} vs expected {mon.expected_settled_amount}."
                ),
            )

        # 9. Clean Exact Match (Precedence #10)
        return (
            ExceptionType.EXACT_MATCH,
            "EXACT_MATCH_VERIFIED",
            "3-way reconciliation verified across payment, settlement, and ledger.",
        )
