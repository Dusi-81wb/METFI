"""
Unit tests for AI Context Builder and Security Boundary isolation.
"""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.canonical import (
    CanonicalPayment,
    CanonicalSettlement,
    CanonicalTransactionGroup,
)
from app.domain.enums import ExceptionType, PaymentStatus, PolicyOutcome, SettlementStatus
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.reconciliation_result import ReconciliationResult
from app.intelligence.context_builder import AIContextBuilder, sanitize_untrusted_text


def _build_test_reconciliation_result(
    case_id: str = "case_ctx_01",
    classification: ExceptionType = ExceptionType.AMOUNT_MISMATCH,
    policy_outcome: PolicyOutcome = PolicyOutcome.REVIEW_REQUIRED,
    is_policy_known: bool = True,
) -> ReconciliationResult:
    monetary = MonetaryEvidence(
        payment_gross=Decimal("1000.00"),
        settled_net=Decimal("976.40"),
        fee_deducted=Decimal("20.00"),
        fee_tax_deducted=Decimal("3.60"),
        total_deductions=Decimal("23.60"),
        settlement_amount_delta=Decimal("0.00"),
        standard_contract_fee=Decimal("20.00"),
        standard_contract_fee_tax=Decimal("3.60"),
        fee_variance=Decimal("0.00"),
        tax_variance=Decimal("0.00"),
        is_fee_policy_known=is_policy_known,
    )
    currency = CurrencyEvidence(
        payment_currency="INR",
        settlement_currency="INR",
        ledger_currency="INR",
        is_currency_matched=True,
    )
    timing = TimingEvidence(
        payment_timestamp="2026-08-30T10:00:00Z",
        settlement_timestamp="2026-08-30T14:00:00Z",
        hours_to_settlement=4.0,
        is_within_sla_window=True,
    )
    reference = ReferenceEvidence(
        payment_id="PAY_001",
        settlement_payment_id="PAY_001",
        payment_order_id="ORD_001",
        ledger_order_id="ORD_001",
        is_payment_id_matched=True,
        is_order_id_matched=True,
    )
    cardinality = CardinalityEvidence(
        payment_count=1,
        settlement_count=1,
        ledger_entry_count=2,
    )
    evidence = ReconciliationEvidence(
        monetary=monetary,
        currency=currency,
        timing=timing,
        reference=reference,
        cardinality=cardinality,
    )
    return ReconciliationResult(
        case_id=case_id,
        order_id="ORD_001",
        classification=classification,
        policy_outcome=policy_outcome,
        confidence=1.0,
        evidence=evidence,
        reason_code="RULE_FEE_COMPLIANT",
        summary="Deterministic fee compliant reconciliation",
        reconciled_at="2026-08-30T15:00:00Z",
    )


def test_sanitize_untrusted_text() -> None:
    # Test stripping control characters
    raw = "Normal text\x00\x08with\x1f control\x7f chars"
    sanitized = sanitize_untrusted_text(raw)
    assert sanitized == "Normal textwith control chars"

    # Test truncation
    long_text = "A" * 300
    sanitized_long = sanitize_untrusted_text(long_text, max_length=100)
    assert len(sanitized_long) <= 120
    assert "[TRUNCATED]" in sanitized_long

    # Test None / empty
    assert sanitize_untrusted_text(None) == ""
    assert sanitize_untrusted_text("") == ""


def test_context_builder_known_policy() -> None:
    rec_result = _build_test_reconciliation_result(is_policy_known=True)
    policy = FeeTaxPolicy(fee_rate=Decimal("0.02"), tax_rate_on_fee=Decimal("0.18"))

    ctx = AIContextBuilder.build_case_context(
        case_id="case_ctx_01",
        deterministic_result=rec_result,
        fee_policy=policy,
    )

    assert "=== RECONCILIATION CASE FOR INVESTIGATION ===" in ctx.rendered_text
    assert "payment.gross_amount: 1000.00" in ctx.rendered_text
    assert "settlement.settled_net: 976.40" in ctx.rendered_text
    assert "fee_policy.fee_rate: 0.02" in ctx.rendered_text
    assert ctx.is_fee_policy_known is True
    assert "payment.gross_amount" in ctx.valid_field_paths
    assert "fee_policy.fee_rate" in ctx.valid_field_paths


def test_context_builder_unknown_policy() -> None:
    rec_result = _build_test_reconciliation_result(is_policy_known=False)

    ctx = AIContextBuilder.build_case_context(
        case_id="case_ctx_02",
        deterministic_result=rec_result,
        fee_policy=None,
    )

    assert "fee_policy.status: UNKNOWN / NOT CONFIGURED" in ctx.rendered_text
    assert "Do NOT assume or invent fee/tax rates" in ctx.rendered_text
    assert ctx.is_fee_policy_known is False
    assert ctx.valid_field_paths["fee_policy.status"] == "UNKNOWN"


def test_context_builder_untrusted_source_records() -> None:
    rec_result = _build_test_reconciliation_result()
    payment = CanonicalPayment(
        payment_id="PAY_999",
        order_id="ORD_999",
        customer_id="CUST_999",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentStatus.SUCCESS,
        payment_timestamp=datetime.now(UTC),
        metadata={"user_note": "Normal transaction"},
    )
    settlement = CanonicalSettlement(
        settlement_id="SET_999",
        payment_id="PAY_999",
        settled_amount=Decimal("976.40"),
        currency="INR",
        settlement_timestamp=datetime.now(UTC),
        fee=Decimal("20.00"),
        fee_tax=Decimal("3.60"),
        status=SettlementStatus.SETTLED,
        metadata={"batch": "BATCH_01"},
    )
    group = CanonicalTransactionGroup(
        case_id="case_ctx_03",
        order_id="ORD_999",
        payment=payment,
        settlement=settlement,
        settlements=[settlement],
        ledger_entries=[],
    )

    ctx = AIContextBuilder.build_case_context(
        case_id="case_ctx_03",
        deterministic_result=rec_result,
        group=group,
    )

    assert "--- [UNTRUSTED SOURCE RECORD DETAILS] ---" in ctx.rendered_text
    assert "payment.payment_id: PAY_999" in ctx.rendered_text
    assert "settlement.settlement_id: SET_999" in ctx.rendered_text
    assert "payment.payment_id" in ctx.valid_field_paths
