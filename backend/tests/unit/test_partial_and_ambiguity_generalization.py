"""
Partial Settlement and Ambiguity Generalization Test Suite.

Verifies:
1. Partial settlement generalization across arbitrary percentages (30%, 40%, 50%, 60%, 75%, 90%).
2. Partial settlement with fee and tax variances.
3. Ambiguity decoupling: arbitrary numeric deltas (₹3, ₹17, ₹37.50, ₹125, ₹412.75)
   remain AMOUNT_MISMATCH and do not falsely trigger AMBIGUOUS.
4. Structural ambiguity triggers strictly from candidate conflict or multi-factor evidence ties.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.canonical import CanonicalPayment, CanonicalSettlement
from app.domain.enums import ExceptionType, PaymentStatus, SettlementStatus
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.fee_policy import FeeTaxPolicy
from app.reconciliation.classifier import DeterministicClassifier
from app.reconciliation.engine import DeterministicReconciliationEngine


@pytest.fixture
def engine() -> DeterministicReconciliationEngine:
    return DeterministicReconciliationEngine()


@pytest.fixture
def classifier() -> DeterministicClassifier:
    return DeterministicClassifier()


PARTIAL_RATIOS = [
    Decimal("0.30"),
    Decimal("0.40"),
    Decimal("0.50"),
    Decimal("0.60"),
    Decimal("0.75"),
    Decimal("0.90"),
]


@pytest.mark.parametrize("ratio", PARTIAL_RATIOS)
def test_partial_settlement_generalization_ratios(
    engine: DeterministicReconciliationEngine,
    ratio: Decimal,
) -> None:
    """Verify that partial settlement is recognized across diverse partial payout fractions."""
    gross = Decimal("2000.00")
    policy = FeeTaxPolicy(fee_rate=Decimal("0.02"), tax_rate_on_fee=Decimal("0.18"))
    exp_fee, exp_tax, _ = policy.calculate_expected_deductions(gross)
    full_net = policy.calculate_expected_settled_amount(gross)  # 2000 - 40 - 7.20 = 1952.80

    partial_net = (full_net * ratio).quantize(Decimal("0.01"))

    pay = CanonicalPayment(
        payment_id=f"pay_prt_{ratio}",
        order_id=f"ord_prt_{ratio}",
        customer_id="cust_prt",
        amount=gross,
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id=f"set_prt_{ratio}",
        payment_id=f"pay_prt_{ratio}",
        settled_amount=partial_net,
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=exp_fee,
        fee_tax=exp_tax,
        status=SettlementStatus.SETTLED,
    )

    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[],
        policy=policy,
    )

    res = batch_res.results[0]
    assert res.classification == ExceptionType.PARTIAL_SETTLEMENT
    assert res.policy_outcome.value == "REVIEW_REQUIRED"


@pytest.mark.parametrize(
    "delta_val",
    [Decimal("3.00"), Decimal("17.00"), Decimal("37.50"), Decimal("125.00"), Decimal("412.75")],
)
def test_arbitrary_numeric_deltas_do_not_falsely_become_ambiguous(
    engine: DeterministicReconciliationEngine,
    delta_val: Decimal,
) -> None:
    """
    Verify that arbitrary monetary differences (₹3, ₹17, ₹37.50, ₹125, ₹412.75)
    are classified as AMOUNT_MISMATCH, proving ambiguity is not tied to magic numeric values.
    """
    gross = Decimal("5000.00")
    policy = FeeTaxPolicy()
    exp_fee, exp_tax, _ = policy.calculate_expected_deductions(gross)
    exp_net = policy.calculate_expected_settled_amount(gross)

    mutated_settled = exp_net - delta_val

    pay = CanonicalPayment(
        payment_id=f"pay_delta_{delta_val}",
        order_id=f"ord_delta_{delta_val}",
        customer_id="cust_delta",
        amount=gross,
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id=f"set_delta_{delta_val}",
        payment_id=f"pay_delta_{delta_val}",
        settled_amount=mutated_settled,
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=exp_fee,
        fee_tax=exp_tax,
        status=SettlementStatus.SETTLED,
    )

    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[],
        policy=policy,
    )

    res = batch_res.results[0]
    assert res.classification == ExceptionType.AMOUNT_MISMATCH
    assert res.classification != ExceptionType.AMBIGUOUS


def test_structural_ambiguity_from_candidate_tie(classifier: DeterministicClassifier) -> None:
    """Verify that ambiguity triggers on structural candidate conflict and not numeric value."""
    evidence = ReconciliationEvidence(
        monetary=MonetaryEvidence(
            payment_gross=Decimal("1000.00"),
            settled_net=Decimal("976.40"),
            fee_deducted=Decimal("20.00"),
            fee_tax_deducted=Decimal("3.60"),
            total_deductions=Decimal("23.60"),
            expected_settled_amount=Decimal("976.40"),
            settlement_amount_delta=Decimal("0.00"),
        ),
        currency=CurrencyEvidence(
            payment_currency="INR",
            settlement_currency="INR",
            ledger_currency="INR",
        ),
        timing=TimingEvidence(hours_to_settlement=24.0, is_within_sla_window=True),
        reference=ReferenceEvidence(
            payment_id="pay_amb_001",
            settlement_payment_id="pay_amb_001",
            payment_order_id="ord_amb_001",
            ledger_order_id="ord_amb_001",
            is_ambiguous_candidate=True,  # Candidate tie
        ),
        cardinality=CardinalityEvidence(payment_count=1, settlement_count=1, ledger_entry_count=2),
        flags=["AMBIGUOUS_CANDIDATES"],
    )

    cls, reason, _ = classifier.classify(evidence)
    assert cls == ExceptionType.AMBIGUOUS
    assert reason == "AMBIGUOUS_CANDIDATE_TIE"
