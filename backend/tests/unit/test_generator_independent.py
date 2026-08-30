"""
Independent Reconciliation Test Suite.

Mandatory Regression Requirement:
This test suite executes deterministic reconciliation EXCLUSIVELY on hand-built canonical
records with ZERO dependencies or imports from SyntheticFinancialGenerator.
"""

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.enums import (
    ExceptionType,
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    SettlementStatus,
)
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.normalizer import (
    normalize_ledger,
    normalize_payment,
    normalize_settlement,
)
from app.domain.raw_models import (
    RawLedgerRecord,
    RawPaymentRecord,
    RawSettlementRecord,
)
from app.reconciliation.engine import DeterministicReconciliationEngine


@pytest.fixture
def engine() -> DeterministicReconciliationEngine:
    return DeterministicReconciliationEngine()


def test_generator_independent_exact_match(engine: DeterministicReconciliationEngine) -> None:
    """Verify clean 3-way exact match without generator."""
    pay = CanonicalPayment(
        payment_id="pay_manual_001",
        order_id="ord_manual_001",
        customer_id="cust_manual_001",
        amount=Decimal("1500.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    # 2% fee = 30.00, 18% tax on fee = 5.40, net = 1464.60
    settle = CanonicalSettlement(
        settlement_id="set_manual_001",
        payment_id="pay_manual_001",
        settled_amount=Decimal("1464.60"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=Decimal("30.00"),
        fee_tax=Decimal("5.40"),
        status=SettlementStatus.SETTLED,
    )
    led_dr = CanonicalLedgerEntry(
        ledger_id="led_manual_001_dr",
        order_id="ord_manual_001",
        debit=Decimal("1500.00"),
        credit=Decimal("0.00"),
        currency="INR",
        entry_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
        status=LedgerStatus.POSTED,
    )
    led_cr = CanonicalLedgerEntry(
        ledger_id="led_manual_001_cr",
        order_id="ord_manual_001",
        debit=Decimal("0.00"),
        credit=Decimal("1500.00"),
        currency="INR",
        entry_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        account=LedgerAccount.ACCOUNTS_RECEIVABLE,
        status=LedgerStatus.POSTED,
    )

    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[led_dr, led_cr],
        dataset_id="independent_test",
    )

    assert batch_res.total_cases == 1
    res = batch_res.results[0]
    assert res.classification == ExceptionType.EXACT_MATCH
    assert res.policy_outcome.value == "AUTO_RECONCILE"


def test_generator_independent_custom_policy(engine: DeterministicReconciliationEngine) -> None:
    """Verify custom fee/tax policy reconciliation without generator."""
    custom_policy = FeeTaxPolicy(
        fee_rate=Decimal("0.03"),  # 3% fee
        tax_rate_on_fee=Decimal("0.10"),  # 10% tax
    )
    # Gross = 10,000.00, Fee = 300.00, Tax = 30.00, Net = 9670.00
    pay = CanonicalPayment(
        payment_id="pay_cust_001",
        order_id="ord_cust_001",
        customer_id="cust_cust_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id="set_cust_001",
        payment_id="pay_cust_001",
        settled_amount=Decimal("9670.00"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=Decimal("300.00"),
        fee_tax=Decimal("30.00"),
        status=SettlementStatus.SETTLED,
    )

    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[],
        policy=custom_policy,
    )

    res = batch_res.results[0]
    assert res.classification == ExceptionType.EXACT_MATCH
    assert res.evidence.monetary.fee_variance == Decimal("0.00")
    assert res.evidence.monetary.tax_variance == Decimal("0.00")


def test_generator_independent_unknown_policy_safe_routing(
    engine: DeterministicReconciliationEngine,
) -> None:
    """Verify that unknown fee policy does NOT fabricate deductions and routes safely."""
    pay = CanonicalPayment(
        payment_id="pay_unk_001",
        order_id="ord_unk_001",
        customer_id="cust_unk_001",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    )
    settle = CanonicalSettlement(
        settlement_id="set_unk_001",
        payment_id="pay_unk_001",
        settled_amount=Decimal("4900.00"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        fee=Decimal("80.00"),
        fee_tax=Decimal("20.00"),
        status=SettlementStatus.SETTLED,
    )

    # Reconcile with policy=None (unknown policy)
    batch_res = engine.reconcile_batch(
        payments=[pay],
        settlements=[settle],
        ledger_entries=[],
        policy=None,
    )

    res = batch_res.results[0]
    # Unknown policy routes to REVIEW_REQUIRED due to unverified fee schedule flag
    assert not res.evidence.monetary.is_fee_policy_known
    assert "UNKNOWN_FEE_POLICY" in res.evidence.flags
    assert res.policy_outcome.value == "REVIEW_REQUIRED"


def test_generator_deletion_regression(engine: DeterministicReconciliationEngine) -> None:
    """
    Verify that independent fixture reconciliation succeeds even when
    synthetic generator modules are completely inaccessible / unimported.
    """
    fixtures_dir = Path(__file__).parent.parent / "fixtures" / "reconciliation_independent"
    assert fixtures_dir.exists(), "Independent fixtures directory must exist"

    # Simulate total isolation from generator package
    generator_modules = {
        "app.services.data_generator": None,
        "app.domain.corruption": None,
    }
    with patch.dict(sys.modules, generator_modules):
        for fpath in fixtures_dir.glob("*.json"):
            with open(fpath, encoding="utf-8") as f:
                scenarios = json.load(f)

            for sc in scenarios:
                p_data = sc.get("payment")
                s_data = sc.get("settlement")
                s_list_data = sc.get("settlements")
                led_list_data = sc.get("ledger_entries", [])
                pol_data = sc.get("policy")
                exp_cls = ExceptionType(sc["expected_classification"])

                payment = (
                    normalize_payment(RawPaymentRecord.model_validate(p_data)) if p_data else None
                )
                settlements = []
                if s_list_data:
                    settlements = [
                        normalize_settlement(RawSettlementRecord.model_validate(s))
                        for s in s_list_data
                    ]
                elif s_data:
                    settlements = [normalize_settlement(RawSettlementRecord.model_validate(s_data))]

                ledger_entries = [
                    normalize_ledger(RawLedgerRecord.model_validate(le)) for le in led_list_data
                ]
                if "competing_ledger_orders" in sc:
                    for clo in sc["competing_ledger_orders"]:
                        for ent in clo.get("entries", []):
                            ledger_entries.append(
                                normalize_ledger(RawLedgerRecord.model_validate(ent))
                            )

                policy = (
                    FeeTaxPolicy(
                        fee_rate=Decimal(str(pol_data["fee_rate"])),
                        tax_rate_on_fee=Decimal(str(pol_data.get("tax_rate_on_fee", "0.18"))),
                    )
                    if pol_data
                    else None
                )

                payments_list = [payment] if payment else []
                res_batch = engine.reconcile_batch(
                    payments=payments_list,
                    settlements=settlements,
                    ledger_entries=ledger_entries,
                    dataset_id="isolated_regression",
                    policy=policy,
                )

                target_res = res_batch.results[0]
                assert target_res.classification == exp_cls, (
                    f"Scenario {sc.get('scenario_id')} failed under generator deletion isolation. "
                    f"Expected {exp_cls}, got {target_res.classification} "
                    f"[{target_res.reason_code}]"
                )
