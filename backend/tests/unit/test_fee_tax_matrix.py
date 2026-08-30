"""
Fee and Tax Policy Matrix Verification Suite.

Tests combinations across configurable fee and tax rates:
Fee schedules: 1.5%, 2.0%, 2.5%, 3.0%, 3.5%
Tax schedules: 0%, 5%, 10%, 18%, 25%
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.canonical import CanonicalPayment, CanonicalSettlement
from app.domain.enums import ExceptionType, PaymentStatus, SettlementStatus
from app.domain.fee_policy import FeeTaxPolicy
from app.reconciliation.engine import DeterministicReconciliationEngine


@pytest.fixture
def engine() -> DeterministicReconciliationEngine:
    return DeterministicReconciliationEngine()


FEE_RATES = [
    Decimal("0.015"),
    Decimal("0.020"),
    Decimal("0.025"),
    Decimal("0.030"),
    Decimal("0.035"),
]
TAX_RATES = [
    Decimal("0.00"),
    Decimal("0.05"),
    Decimal("0.10"),
    Decimal("0.18"),
    Decimal("0.25"),
]


@pytest.mark.parametrize("fee_rate", FEE_RATES)
@pytest.mark.parametrize("tax_rate", TAX_RATES)
def test_fee_tax_matrix_exact_match(
    engine: DeterministicReconciliationEngine,
    fee_rate: Decimal,
    tax_rate: Decimal,
) -> None:
    """Verify that every policy in the matrix produces clean EXACT_MATCH for compliant records."""
    policy = FeeTaxPolicy(fee_rate=fee_rate, tax_rate_on_fee=tax_rate)
    gross = Decimal("10000.00")
    exp_fee, exp_tax, total_ded = policy.calculate_expected_deductions(gross)
    exp_net = policy.calculate_expected_settled_amount(gross)

    pay = CanonicalPayment(
        payment_id=f"pay_{fee_rate}_{tax_rate}",
        order_id=f"ord_{fee_rate}_{tax_rate}",
        customer_id="cust_matrix",
        amount=gross,
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id=f"set_{fee_rate}_{tax_rate}",
        payment_id=f"pay_{fee_rate}_{tax_rate}",
        settled_amount=exp_net,
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
    assert res.classification == ExceptionType.EXACT_MATCH
    assert res.evidence.monetary.fee_variance == Decimal("0.00")
    assert res.evidence.monetary.tax_variance == Decimal("0.00")
    assert res.policy_outcome.value == "AUTO_RECONCILE"


@pytest.mark.parametrize("fee_rate", FEE_RATES)
@pytest.mark.parametrize("tax_rate", TAX_RATES)
def test_fee_tax_matrix_tax_variance_detection(
    engine: DeterministicReconciliationEngine,
    fee_rate: Decimal,
    tax_rate: Decimal,
) -> None:
    """Verify tax variance detection when observed tax deviates from active policy."""
    policy = FeeTaxPolicy(fee_rate=fee_rate, tax_rate_on_fee=tax_rate)
    gross = Decimal("10000.00")
    exp_fee = policy.calculate_expected_fee(gross)

    # Inject incorrect tax rate (e.g. tax is 15.00 different)
    mutated_tax = (exp_fee * Decimal("0.12")).quantize(Decimal("0.01"))
    if mutated_tax == policy.calculate_expected_tax(exp_fee):
        mutated_tax += Decimal("10.00")

    observed_total_ded = exp_fee + mutated_tax
    settled_net = gross - observed_total_ded

    pay = CanonicalPayment(
        payment_id=f"pay_taxvar_{fee_rate}_{tax_rate}",
        order_id=f"ord_taxvar_{fee_rate}_{tax_rate}",
        customer_id="cust_matrix",
        amount=gross,
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id=f"set_taxvar_{fee_rate}_{tax_rate}",
        payment_id=f"pay_taxvar_{fee_rate}_{tax_rate}",
        settled_amount=settled_net,
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=exp_fee,
        fee_tax=mutated_tax,
        status=SettlementStatus.SETTLED,
    )

    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[],
        policy=policy,
    )

    res = batch_res.results[0]
    assert res.classification == ExceptionType.FEE_DISCREPANCY
    assert "TAX_VARIANCE_DETECTED" in res.evidence.flags or res.reason_code in [
        "TAX_VARIANCE_DETECTED",
        "FEE_TAX_VARIANCE_DETECTED",
    ]
    assert res.evidence.monetary.tax_variance != Decimal("0.00")
