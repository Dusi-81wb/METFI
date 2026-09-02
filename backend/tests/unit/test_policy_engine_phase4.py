"""
Unit tests for DeterministicPolicyEngine authorization gates and safety checks.
"""

from decimal import Decimal

from app.domain.action import ActionType
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.investigation import (
    BoundedRecommendation,
    EvidenceReference,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecisionOutcome,
    RetryPolicy,
    VarianceTolerancePolicy,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.policy.policy_engine import DeterministicPolicyEngine


def _build_test_context(
    classification: ExceptionType = ExceptionType.EXACT_MATCH,
    payment_amount: Decimal = Decimal("1000.00"),
    settlement_amount: Decimal = Decimal("1000.00"),
    fee_variance: Decimal = Decimal("0.00"),
    tax_variance: Decimal = Decimal("0.00"),
    is_fee_policy_known: bool = True,
    verifier_status: VerifierStatus = VerifierStatus.VERIFIED,
) -> tuple[ReconciliationResult, VerifiedInvestigationEnvelope]:
    monetary = MonetaryEvidence(
        payment_gross=payment_amount,
        settled_net=settlement_amount,
        fee_variance=fee_variance,
        tax_variance=tax_variance,
        is_fee_policy_known=is_fee_policy_known,
    )
    evidence = ReconciliationEvidence(
        monetary=monetary,
        currency=CurrencyEvidence(
            payment_currency="INR",
            settlement_currency="INR",
            is_currency_matched=(classification != ExceptionType.CURRENCY_MISMATCH),
        ),
        timing=TimingEvidence(
            payment_timestamp="2026-08-30T10:00:00Z",
            settlement_timestamp="2026-08-30T12:00:00Z",
            hours_to_settlement=2.0,
            is_within_sla_window=True,
        ),
        reference=ReferenceEvidence(),
        cardinality=CardinalityEvidence(),
    )
    rec_result = ReconciliationResult(
        case_id="case_tst_01",
        order_id="ORD-TST-01",
        classification=classification,
        policy_outcome=PolicyOutcome.AUTO_RECONCILE
        if classification == ExceptionType.EXACT_MATCH
        else PolicyOutcome.REVIEW_REQUIRED,
        evidence=evidence,
        reason_code="RULE_TEST",
        summary="Test reconciliation summary",
        reconciled_at="2026-08-30T12:00:00Z",
    )

    inv_result = InvestigationResult(
        case_id="case_tst_01",
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Fee deduction identified.",
        evidence_references=[
            EvidenceReference(
                field_path="monetary.payment_amount",
                observed_value=str(payment_amount),
                significance="Payment amount",
            )
        ],
        recommended_action=BoundedRecommendation.AUTO_RECONCILE,
    )
    ver_result = VerificationResult(
        investigation_id=inv_result.investigation_id,
        case_id="case_tst_01",
        verifier_status=verifier_status,
        is_evidence_supported=(verifier_status == VerifierStatus.VERIFIED),
        are_references_valid=(verifier_status == VerifierStatus.VERIFIED),
        is_deterministic_truth_preserved=(classification != ExceptionType.CURRENCY_MISMATCH),
        is_recommendation_safe=(verifier_status == VerifierStatus.VERIFIED),
        verifier_notes="Verification test note",
    )
    envelope = VerifiedInvestigationEnvelope(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        investigation=inv_result,
        verification=ver_result,
        final_canonical_status=classification,
        final_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        summary="Test summary",
    )
    return rec_result, envelope


def test_clean_exact_match_authorizes_auto_reconcile() -> None:
    rec_result, envelope = _build_test_context(classification=ExceptionType.EXACT_MATCH)
    engine = DeterministicPolicyEngine()
    policy_config = DomainPolicyConfig(
        fee_tax_policy=FeeTaxPolicy(fee_rate=Decimal("0.02"), tax_rate_on_fee=Decimal("0.18"))
    )

    decision, precond = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        policy_config=policy_config,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.decision == PolicyDecisionOutcome.ALLOW
    assert decision.is_autonomous_authorized is True
    assert precond.is_all_satisfied() is True
    assert "ALLOW_AUTO_RECONCILE" in decision.reason_codes


def test_unknown_fee_policy_fails_closed() -> None:
    # Amount mismatch where fee policy is unconfigured
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.AMOUNT_MISMATCH,
        is_fee_policy_known=False,
    )
    engine = DeterministicPolicyEngine()
    policy_config = DomainPolicyConfig(fee_tax_policy=None)

    decision, precond = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        policy_config=policy_config,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.is_autonomous_authorized is False
    assert precond.is_policy_known is False
    assert "ERR_UNKNOWN_FEE_POLICY" in decision.reason_codes


def test_currency_mismatch_blocks_auto_reconcile() -> None:
    # Currency mismatch: AI attempts to recommend AUTO_RECONCILE
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.CURRENCY_MISMATCH,
    )
    engine = DeterministicPolicyEngine()

    decision, precond = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.is_autonomous_authorized is False
    assert precond.is_deterministic_truth_preserved is False
    assert "ERR_BLOCKING_CLASSIFICATION_CONFLICT" in decision.reason_codes


def test_verifier_rejection_blocks_auto_reconcile() -> None:
    # Verifier rejected the AI investigation
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.AMOUNT_MISMATCH,
        verifier_status=VerifierStatus.REJECTED,
    )
    engine = DeterministicPolicyEngine()

    decision, precond = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.is_autonomous_authorized is False
    assert precond.is_verifier_passed is False
    assert "ERR_VERIFIER_NOT_PASSED" in decision.reason_codes


def test_fee_variance_exceeding_tolerance_denies_auto_reconcile() -> None:
    # Fee variance of 15.00 exceeds standard tolerance of 1.00
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.AMOUNT_MISMATCH,
        fee_variance=Decimal("15.00"),
    )
    engine = DeterministicPolicyEngine()
    policy_config = DomainPolicyConfig(
        variance_tolerance=VarianceTolerancePolicy(max_absolute_fee_variance=Decimal("1.00"))
    )

    decision, precond = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        policy_config=policy_config,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.decision == PolicyDecisionOutcome.DENY
    assert decision.is_autonomous_authorized is False
    assert precond.is_within_variance_tolerance is False
    assert "ERR_FEE_VARIANCE_EXCEEDS_TOLERANCE" in decision.reason_codes


def test_retry_limits_enforced() -> None:
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.MISSING_SETTLEMENT,
    )
    engine = DeterministicPolicyEngine()
    policy_config = DomainPolicyConfig(retry_policy=RetryPolicy(max_retry_attempts=2))

    # Attempt 1: Authorized
    d1, p1 = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        policy_config=policy_config,
        requested_action=ActionType.REQUEST_RETRY,
        retry_count=1,
    )
    assert d1.decision == PolicyDecisionOutcome.ALLOW
    assert p1.is_within_retry_limit is True

    # Attempt 3: Denied (exceeds max 2)
    d2, p2 = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        policy_config=policy_config,
        requested_action=ActionType.REQUEST_RETRY,
        retry_count=3,
    )
    assert d2.decision == PolicyDecisionOutcome.DENY
    assert p2.is_within_retry_limit is False
    assert "ERR_RETRY_LIMIT_EXCEEDED" in d2.reason_codes


def test_manual_review_and_escalation_always_allowed() -> None:
    # Even if case is heavily faulted, manual review and escalation are allowed
    rec_result, envelope = _build_test_context(
        classification=ExceptionType.AMBIGUOUS,
        verifier_status=VerifierStatus.REJECTED,
    )
    engine = DeterministicPolicyEngine()

    d_rev, _ = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        requested_action=ActionType.MARK_FOR_REVIEW,
    )
    assert d_rev.decision == PolicyDecisionOutcome.ALLOW

    d_esc, _ = engine.evaluate_action_authorization(
        case_id="case_tst_01",
        deterministic_result=rec_result,
        envelope=envelope,
        requested_action=ActionType.ESCALATE,
    )
    assert d_esc.decision == PolicyDecisionOutcome.ALLOW
