"""
Unit tests for Action Idempotency and Concurrency Protection.
"""

import asyncio

import pytest

from app.domain.action import (
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
)
from app.policy.executor import SimulationActionExecutor


@pytest.mark.asyncio
async def test_repeated_execution_returns_idempotent_result() -> None:
    executor = SimulationActionExecutor()
    action = ControlledAction(
        case_id="case_idemp_01",
        action_type=ActionType.AUTO_RECONCILE,
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_unique_key_01",
    )

    # First Execution
    a1, r1, e1 = await executor.execute_action(action)
    assert a1.state == ActionState.EXECUTED
    assert r1.status == ActionState.EXECUTED

    # Second Execution (same action & key)
    a2, r2, e2 = await executor.execute_action(action)
    assert a2.state == ActionState.EXECUTED
    assert r2.status == ActionState.EXECUTED
    assert r1.action_id == r2.action_id
    assert r1.executed_at == r2.executed_at


@pytest.mark.asyncio
async def test_concurrent_duplicate_executions_safely_serialized() -> None:
    executor = SimulationActionExecutor()
    action = ControlledAction(
        case_id="case_conc_01",
        action_type=ActionType.REQUEST_RETRY,
        state=ActionState.AUTHORIZED,
        authorization_status=AuthorizationStatus.AUTHORIZED,
        idempotency_key="idemp_concurrent_key_01",
    )

    # Launch 5 concurrent execution tasks simultaneously
    results = await asyncio.gather(
        executor.execute_action(action),
        executor.execute_action(action),
        executor.execute_action(action),
        executor.execute_action(action),
        executor.execute_action(action),
    )

    # All returned actions and results must be identical and executed
    for act, res, _ in results:
        assert act.state == ActionState.EXECUTED
        assert res.action_id == results[0][1].action_id
        assert res.executed_at == results[0][1].executed_at
