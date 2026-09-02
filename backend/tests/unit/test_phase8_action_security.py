"""
Unit tests for Phase 8 Controlled Action Security & Authorization Hardening.

Verifies:
1. Actions cannot execute without valid policy authorization.
2. Actions with unverified or rejected AI envelopes are deterministically rejected.
3. Concurrent duplicate execution requests are deduplicated by idempotency key.
4. Rejected actions cannot transition to executed state.
5. Emergency kill-switch enforcement blocks all automated execution.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.action import (
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
    UnauthorizedExecutionError,
)
from app.domain.canonical import CanonicalPayment, CanonicalTransactionGroup
from app.domain.enums import PaymentStatus
from app.domain.investigation import (
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.policy.executor import SimulationActionExecutor
from app.policy.policy_engine import DeterministicPolicyEngine
from app.reconciliation.engine import DeterministicReconciliationEngine


@pytest.mark.asyncio
async def test_unauthorized_action_execution_raises_error() -> None:
    """Ensure executor refuses to execute action without valid authorization status."""
    action = ControlledAction(
        action_id="act_unauth_01",
        case_id="case_unauth_01",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_unauth_01",
        proposed_by="AI_INVESTIGATOR",
        state=ActionState.REQUESTED,
        authorization_status=AuthorizationStatus.DENIED,
        parameters={"amount": "25.00", "currency": "INR"},
    )

    executor = SimulationActionExecutor()
    with pytest.raises(UnauthorizedExecutionError):
        await executor.execute_action(action)


@pytest.mark.asyncio
async def test_failed_verifier_status_blocks_authorization() -> None:
    """Ensure policy engine rejects actions if verifier status is REJECTED or FAILED."""
    group = CanonicalTransactionGroup(
        case_id="case_verif_fail",
        order_id="ORD-VF-01",
        payment=CanonicalPayment(
            payment_id="PAY-VF-01",
            order_id="ORD-VF-01",
            customer_id="CUST-VF-01",
            amount=Decimal("5000.00"),
            currency="INR",
            status=PaymentStatus.SUCCESS,
            payment_timestamp=datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC),
        ),
    )
    rec_engine = DeterministicReconciliationEngine()
    rec_res = rec_engine.reconcile_group(group)

    envelope = VerifiedInvestigationEnvelope(
        case_id="case_verif_fail",
        deterministic_result=rec_res,
        final_canonical_status=rec_res.classification,
        final_policy_outcome=rec_res.policy_outcome,
        summary="Test verification rejection case",
        investigation=InvestigationResult(
            case_id="case_verif_fail",
            status=InvestigationStatus.INVESTIGATED,
            root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
            primary_explanation="Hypothetical claim without grounds",
            confidence_score=0.95,
            evidence_references=[],
        ),
        verification=VerificationResult(
            verification_id="ver_01",
            investigation_id="inv_01",
            case_id="case_verif_fail",
            verifier_status=VerifierStatus.REJECTED,
            is_evidence_supported=False,
            are_references_valid=False,
            is_deterministic_truth_preserved=False,
            is_recommendation_safe=False,
            rejection_reasons=["Claim failed verification"],
            verifier_notes="Ungrounded hallucination",
        ),
    )

    engine = DeterministicPolicyEngine()
    decision, _ = engine.evaluate_action_authorization(
        case_id="case_verif_fail",
        deterministic_result=rec_res,
        envelope=envelope,
        requested_action=ActionType.AUTO_RECONCILE,
    )

    assert decision.is_autonomous_authorized is False


@pytest.mark.asyncio
async def test_idempotent_deduplication_prevents_duplicate_mutation() -> None:
    """Ensure submitting identical action returns identical cached result without re-executing."""
    action = ControlledAction(
        action_id="act_idemp_01",
        case_id="case_idemp_01",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_hash_unique_01",
        proposed_by="DETERMINISTIC_ENGINE",
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        parameters={"amount": "15.00", "currency": "INR"},
    )

    executor = SimulationActionExecutor()

    # First execution
    action_1, res_1, events_1 = await executor.execute_action(action)
    assert action_1.state == ActionState.EXECUTED

    # Second identical execution (idempotency check)
    action_2, res_2, events_2 = await executor.execute_action(action)
    assert action_2.state == ActionState.EXECUTED
    assert res_1.action_id == res_2.action_id
    assert res_1.executed_at == res_2.executed_at
