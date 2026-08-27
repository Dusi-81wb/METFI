"""Unit tests for DeterministicPolicyEngine policy gating and safety invariants."""

from decimal import Decimal

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.policy.policy_engine import DeterministicPolicyEngine


def _make_dummy_evidence(flags: list[str] | None = None) -> ReconciliationEvidence:
    return ReconciliationEvidence(
        monetary=MonetaryEvidence(settlement_amount_delta=Decimal("0.00")),
        currency=CurrencyEvidence(is_currency_matched=True),
        timing=TimingEvidence(is_within_sla_window=True),
        reference=ReferenceEvidence(is_order_id_matched=True),
        cardinality=CardinalityEvidence(payment_count=1, settlement_count=1, ledger_entry_count=2),
        flags=flags or [],
    )


def test_policy_exact_match_authorizes_auto_reconcile() -> None:
    policy = DeterministicPolicyEngine()
    ev = _make_dummy_evidence(flags=[])
    outcome = policy.evaluate_policy(ExceptionType.EXACT_MATCH, ev)
    assert outcome == PolicyOutcome.AUTO_RECONCILE


def test_policy_exact_match_with_flags_downgrades_to_review() -> None:
    policy = DeterministicPolicyEngine()
    ev = _make_dummy_evidence(flags=["UNEXPECTED_FLAG"])
    outcome = policy.evaluate_policy(ExceptionType.EXACT_MATCH, ev)
    assert outcome == PolicyOutcome.REVIEW_REQUIRED


def test_policy_reviewable_exceptions() -> None:
    policy = DeterministicPolicyEngine()
    ev = _make_dummy_evidence(flags=["AMOUNT_DELTA_NON_ZERO"])
    assert (
        policy.evaluate_policy(ExceptionType.AMOUNT_MISMATCH, ev) == PolicyOutcome.REVIEW_REQUIRED
    )
    assert (
        policy.evaluate_policy(ExceptionType.DUPLICATE_RECORD, ev) == PolicyOutcome.REVIEW_REQUIRED
    )
    assert policy.evaluate_policy(ExceptionType.DATE_MISMATCH, ev) == PolicyOutcome.REVIEW_REQUIRED
    assert (
        policy.evaluate_policy(ExceptionType.REFERENCE_MISMATCH, ev)
        == PolicyOutcome.REVIEW_REQUIRED
    )
    assert (
        policy.evaluate_policy(ExceptionType.PARTIAL_SETTLEMENT, ev)
        == PolicyOutcome.REVIEW_REQUIRED
    )
    assert (
        policy.evaluate_policy(ExceptionType.FEE_DISCREPANCY, ev) == PolicyOutcome.REVIEW_REQUIRED
    )


def test_policy_unresolved_exceptions() -> None:
    policy = DeterministicPolicyEngine()
    ev = _make_dummy_evidence(flags=["MISSING_SETTLEMENT"])
    assert policy.evaluate_policy(ExceptionType.MISSING_SETTLEMENT, ev) == PolicyOutcome.UNRESOLVED
    assert policy.evaluate_policy(ExceptionType.CURRENCY_MISMATCH, ev) == PolicyOutcome.UNRESOLVED
    assert policy.evaluate_policy(ExceptionType.AMBIGUOUS, ev) == PolicyOutcome.UNRESOLVED
