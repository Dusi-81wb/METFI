"""
Unit tests for SimulationActionExecutor safety boundaries and authorization enforcement.
"""

import pytest

from app.domain.action import (
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
    UnauthorizedExecutionError,
)
from app.domain.audit import AuditEventType
from app.policy.executor import SimulationActionExecutor


@pytest.mark.asyncio
async def test_authorized_action_execution_succeeds() -> None:
    executor = SimulationActionExecutor()
    action = ControlledAction(
        case_id="case_exec_01",
        action_type=ActionType.AUTO_RECONCILE,
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_exec_01",
    )

    final_action, result, events = await executor.execute_action(action)

    assert final_action.state == ActionState.EXECUTED
    assert result.status == ActionState.EXECUTED
    assert "SETTLEMENT_RECORD_MARKED_RECONCILED" in result.side_effects_simulated
    assert any(e.event_type == AuditEventType.ACTION_EXECUTED for e in events)


@pytest.mark.asyncio
async def test_unauthorized_action_execution_rejected() -> None:
    executor = SimulationActionExecutor()
    action = ControlledAction(
        case_id="case_exec_02",
        action_type=ActionType.AUTO_RECONCILE,
        state=ActionState.REQUESTED,
        authorization_status=AuthorizationStatus.DENIED,  # DENIED!
        idempotency_key="idemp_exec_02",
    )

    with pytest.raises(UnauthorizedExecutionError) as excinfo:
        await executor.execute_action(action)

    assert "DENIED" in str(excinfo.value)


@pytest.mark.asyncio
async def test_invalid_state_action_execution_rejected() -> None:
    executor = SimulationActionExecutor()
    action = ControlledAction(
        case_id="case_exec_03",
        action_type=ActionType.AUTO_RECONCILE,
        state=ActionState.VALIDATING,  # Not in AUTHORIZED state!
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_exec_03",
    )

    with pytest.raises(UnauthorizedExecutionError) as excinfo:
        await executor.execute_action(action)

    assert "VALIDATING" in str(excinfo.value)


@pytest.mark.asyncio
async def test_different_action_types_side_effects() -> None:
    executor = SimulationActionExecutor()

    # Retry Action
    retry_action = ControlledAction(
        case_id="case_retry_01",
        action_type=ActionType.REQUEST_RETRY,
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_retry_01",
        payload={"retry_count": 2},
    )
    _, retry_res, _ = await executor.execute_action(retry_action)
    assert "PAYMENT_GATEWAY_RETRY_ENQUEUED" in retry_res.side_effects_simulated

    # Escalate Action
    esc_action = ControlledAction(
        case_id="case_esc_01",
        action_type=ActionType.ESCALATE,
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_esc_01",
    )
    _, esc_res, _ = await executor.execute_action(esc_action)
    assert "CASE_ESCALATED_TO_SENIOR_FINANCE_OPERATIONS" in esc_res.side_effects_simulated
