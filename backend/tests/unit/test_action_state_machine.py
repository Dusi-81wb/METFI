"""
Unit tests for the ControlledAction domain model and strict state machine transitions.
"""

import pytest

from app.domain.action import (
    ActionResult,
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
    InvalidStateTransitionError,
)


def test_controlled_action_creation() -> None:
    action = ControlledAction(
        case_id="case_101",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_abc123",
        requested_by="test_harness",
    )
    assert action.case_id == "case_101"
    assert action.action_type == ActionType.AUTO_RECONCILE
    assert action.state == ActionState.REQUESTED
    assert action.authorization_status == AuthorizationStatus.PENDING_REVIEW
    assert action.action_id.startswith("act_")


def test_valid_state_machine_transitions() -> None:
    # 1. REQUESTED -> VALIDATING
    action = ControlledAction(
        case_id="case_101",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_abc123",
    )
    validating = action.transition_to(ActionState.VALIDATING)
    assert validating.state == ActionState.VALIDATING

    # 2. VALIDATING -> AUTHORIZED
    authorized = validating.transition_to(ActionState.AUTHORIZED)
    assert authorized.state == ActionState.AUTHORIZED
    assert authorized.authorization_status == AuthorizationStatus.AUTHORIZED
    assert authorized.authorized_at is not None

    # 3. AUTHORIZED -> EXECUTING
    executing = authorized.transition_to(ActionState.EXECUTING)
    assert executing.state == ActionState.EXECUTING

    # 4. EXECUTING -> EXECUTED
    result = ActionResult(
        action_id=executing.action_id,
        case_id="case_101",
        action_type=ActionType.AUTO_RECONCILE,
        status=ActionState.EXECUTED,
        side_effects_simulated=["MARKED_RECONCILED"],
    )
    executed = executing.transition_to(ActionState.EXECUTED, execution_result=result)
    assert executed.state == ActionState.EXECUTED
    assert executed.executed_at is not None
    assert executed.execution_result == result


def test_rejection_state_machine_transition() -> None:
    action = ControlledAction(
        case_id="case_102",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_102",
    )
    validating = action.transition_to(ActionState.VALIDATING)
    rejected = validating.transition_to(
        ActionState.REJECTED,
        rejection_reasons=["Unknown fee policy"],
    )
    assert rejected.state == ActionState.REJECTED
    assert rejected.authorization_status == AuthorizationStatus.DENIED
    assert "Unknown fee policy" in rejected.rejection_reasons


def test_illegal_state_machine_transitions_raise_error() -> None:
    action = ControlledAction(
        case_id="case_103",
        action_type=ActionType.AUTO_RECONCILE,
        idempotency_key="idemp_103",
    )
    # Cannot jump directly from REQUESTED to EXECUTED
    with pytest.raises(InvalidStateTransitionError):
        action.transition_to(ActionState.EXECUTED)

    # Cannot jump directly from REQUESTED to EXECUTING
    with pytest.raises(InvalidStateTransitionError):
        action.transition_to(ActionState.EXECUTING)

    validating = action.transition_to(ActionState.VALIDATING)
    authorized = validating.transition_to(ActionState.AUTHORIZED)
    executing = authorized.transition_to(ActionState.EXECUTING)
    result = ActionResult(
        action_id=executing.action_id,
        case_id="case_103",
        action_type=ActionType.AUTO_RECONCILE,
        status=ActionState.EXECUTED,
    )
    executed = executing.transition_to(ActionState.EXECUTED, execution_result=result)

    # Terminal state cannot transition to anything
    with pytest.raises(InvalidStateTransitionError):
        executed.transition_to(ActionState.REQUESTED)


def test_deterministic_idempotency_key_generation() -> None:
    k1 = ControlledAction.generate_idempotency_key(
        case_id="case_999",
        action_type=ActionType.REQUEST_RETRY,
        payload={"retry_count": 1},
        policy_version="1.0.0",
    )
    k2 = ControlledAction.generate_idempotency_key(
        case_id="case_999",
        action_type=ActionType.REQUEST_RETRY,
        payload={"retry_count": 1},
        policy_version="1.0.0",
    )
    k3 = ControlledAction.generate_idempotency_key(
        case_id="case_999",
        action_type=ActionType.REQUEST_RETRY,
        payload={"retry_count": 2},
        policy_version="1.0.0",
    )
    assert k1 == k2
    assert k1 != k3
