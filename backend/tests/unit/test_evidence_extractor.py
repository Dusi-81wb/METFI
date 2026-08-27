"""Unit tests for EvidenceExtractor mathematical and structural evidence evaluation."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.enums import LedgerAccount, LedgerStatus, PaymentStatus, SettlementStatus
from app.reconciliation.evidence_extractor import EvidenceExtractor


def test_evidence_extractor_clean_match() -> None:
    extractor = EvidenceExtractor()
    payment = CanonicalPayment(
        payment_id="pay_01",
        order_id="ord_01",
        customer_id="cust_01",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
        metadata={},
    )
    settlement = CanonicalSettlement(
        settlement_id="set_01",
        payment_id="pay_01",
        settled_amount=Decimal("976.40"),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, 0, tzinfo=UTC),
        status=SettlementStatus.SETTLED,
        metadata={},
    )
    ledger = [
        CanonicalLedgerEntry(
            ledger_id="led_dr",
            order_id="ord_01",
            debit=Decimal("1000.00"),
            credit=Decimal("0.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
            account=LedgerAccount.PAYMENT_GATEWAY_CLEARING,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
        CanonicalLedgerEntry(
            ledger_id="led_cr",
            order_id="ord_01",
            debit=Decimal("0.00"),
            credit=Decimal("1000.00"),
            currency="INR",
            entry_timestamp=datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC),
            account=LedgerAccount.ACCOUNTS_RECEIVABLE,
            status=LedgerStatus.POSTED,
            metadata={},
        ),
    ]

    evidence = extractor.extract_evidence(payment, [settlement], ledger)

    assert evidence.monetary.settlement_amount_delta == Decimal("0.00")
    assert evidence.monetary.fee_variance == Decimal("0.00")
    assert evidence.currency.is_currency_matched is True
    assert evidence.timing.is_within_sla_window is True
    assert evidence.timing.is_settlement_preceding_payment is False
    assert evidence.reference.is_order_id_matched is True
    assert evidence.reference.is_payment_id_matched is True
    assert evidence.cardinality.payment_count == 1
    assert evidence.cardinality.settlement_count == 1
    assert len(evidence.flags) == 0


def test_evidence_extractor_detects_negative_timing() -> None:
    extractor = EvidenceExtractor()
    payment = CanonicalPayment(
        payment_id="pay_02",
        order_id="ord_02",
        customer_id="cust_02",
        amount=Decimal("500.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime(2026, 8, 5, 10, 0, 0, tzinfo=UTC),
        metadata={},
    )
    # Settlement timestamp precedes payment authorization
    settlement = CanonicalSettlement(
        settlement_id="set_02",
        payment_id="pay_02",
        settled_amount=Decimal("488.20"),
        fee=Decimal("10.00"),
        fee_tax=Decimal("1.80"),
        currency="INR",
        settlement_timestamp=datetime(2026, 8, 2, 10, 0, 0, tzinfo=UTC),
        status=SettlementStatus.SETTLED,
        metadata={},
    )

    evidence = extractor.extract_evidence(payment, [settlement], [])
    assert evidence.timing.is_settlement_preceding_payment is True
    assert "SETTLEMENT_PRECEDES_PAYMENT" in evidence.flags
