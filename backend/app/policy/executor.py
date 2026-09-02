"""
Action Execution Layer.

Provides safe, simulated execution of policy-authorized operational actions.

Strict Non-Negotiable Rules:
1. Executor MUST verify valid policy authorization before execution.
2. Direct execution of unauthorized, unapproved, or rejected actions is strictly REJECTED.
3. Every action execution is idempotent. Re-submitting the same action returns the cached result.
4. ZERO real money movement or live financial mutations. All actions run in simulated/test mode.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from app.core.logging import logger
from app.domain.action import (
    ActionResult,
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
    UnauthorizedExecutionError,
)
from app.domain.audit import AuditEvent, AuditEventType


class ActionExecutor(ABC):
    """Abstract base class for controlled action executors."""

    @abstractmethod
    async def execute_action(
        self, action: ControlledAction
    ) -> tuple[ControlledAction, ActionResult, list[AuditEvent]]:
        """
        Execute an authorized operational action and return the updated state.
        """


class SimulationActionExecutor(ActionExecutor):
    """
    Simulation Action Executor for safe development, testing, and demonstration.

    Enforces authorization verification, re-authorization checks, and idempotency.
    """

    def __init__(self) -> None:
        self._executed_cache: dict[
            str, tuple[ControlledAction, ActionResult, list[AuditEvent]]
        ] = {}
        self._concurrency_locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._global_lock:
            if key not in self._concurrency_locks:
                self._concurrency_locks[key] = asyncio.Lock()
            return self._concurrency_locks[key]

    async def execute_action(
        self, action: ControlledAction
    ) -> tuple[ControlledAction, ActionResult, list[AuditEvent]]:
        """
        Execute a policy-authorized action with strict safety validation.
        """
        # Hard Invariant 1: Executor enforces authorization at boundary
        if action.authorization_status != AuthorizationStatus.AUTHORIZED:
            msg = (
                f"Execution rejected: Action {action.action_id} has authorization status "
                f"'{action.authorization_status}', expected '{AuthorizationStatus.AUTHORIZED}'."
            )
            raise UnauthorizedExecutionError(msg)

        if action.state not in (ActionState.AUTHORIZED, ActionState.EXECUTING):
            msg = (
                f"Execution rejected: Action {action.action_id} is in invalid state "
                f"'{action.state}', expected '{ActionState.AUTHORIZED}'."
            )
            raise UnauthorizedExecutionError(msg)

        key = action.idempotency_key
        lock = await self._get_lock(key)

        async with lock:
            # Idempotency Check: Return cached execution result if previously executed
            if key in self._executed_cache:
                cached_action, cached_result, cached_events = self._executed_cache[key]
                logger.info(
                    "Idempotency hit for action %s (key %s). Returning cached result.",
                    action.action_id,
                    key,
                )
                return cached_action, cached_result, cached_events

            perf_start = time.perf_counter()
            audit_events: list[AuditEvent] = []

            # Emit Execution Started Event
            audit_events.append(
                AuditEvent(
                    event_type=AuditEventType.ACTION_EXECUTION_STARTED,
                    case_id=action.case_id,
                    action_id=action.action_id,
                    policy_version=action.policy_version,
                    evidence_references=action.evidence_references,
                    payload={"action_type": action.action_type.value},
                )
            )

            # Transition state to EXECUTING
            executing_action = action.transition_to(ActionState.EXECUTING)

            try:
                side_effects, details = await self._simulate_side_effects(executing_action)
                latency_ms = (time.perf_counter() - perf_start) * 1000.0

                result = ActionResult(
                    action_id=action.action_id,
                    case_id=action.case_id,
                    action_type=action.action_type,
                    status=ActionState.EXECUTED,
                    side_effects_simulated=side_effects,
                    details=details,
                    latency_ms=round(latency_ms, 2),
                )

                final_action = executing_action.transition_to(
                    ActionState.EXECUTED, execution_result=result
                )

                audit_events.append(
                    AuditEvent(
                        event_type=AuditEventType.ACTION_EXECUTED,
                        case_id=action.case_id,
                        action_id=action.action_id,
                        policy_version=action.policy_version,
                        evidence_references=action.evidence_references,
                        payload={
                            "status": "EXECUTED",
                            "side_effects": side_effects,
                            "latency_ms": round(latency_ms, 2),
                        },
                    )
                )

                self._executed_cache[key] = (final_action, result, audit_events)
                return final_action, result, audit_events

            except Exception as e:
                latency_ms = (time.perf_counter() - perf_start) * 1000.0
                error_result = ActionResult(
                    action_id=action.action_id,
                    case_id=action.case_id,
                    action_type=action.action_type,
                    status=ActionState.FAILED,
                    error_message=str(e),
                    latency_ms=round(latency_ms, 2),
                )

                failed_action = executing_action.transition_to(
                    ActionState.FAILED, execution_result=error_result
                )

                audit_events.append(
                    AuditEvent(
                        event_type=AuditEventType.ACTION_EXECUTION_FAILED,
                        case_id=action.case_id,
                        action_id=action.action_id,
                        policy_version=action.policy_version,
                        evidence_references=action.evidence_references,
                        payload={"error": str(e)},
                    )
                )

                return failed_action, error_result, audit_events

    async def _simulate_side_effects(
        self, action: ControlledAction
    ) -> tuple[list[str], dict[str, Any]]:
        """Simulate domain side effects safely based on action type."""
        side_effects: list[str] = []
        details: dict[str, Any] = {"simulation_mode": True}

        if action.action_type == ActionType.AUTO_RECONCILE:
            side_effects.append("SETTLEMENT_RECORD_MARKED_RECONCILED")
            side_effects.append("LEDGER_POSTING_RECONCILED")
            details["reconciliation_timestamp"] = datetime.now(UTC).isoformat()
            details["authorization_code"] = f"AUTH-REC-{action.action_id[:8]}"

        elif action.action_type == ActionType.REQUEST_RETRY:
            side_effects.append("PAYMENT_GATEWAY_RETRY_ENQUEUED")
            details["retry_attempt"] = action.payload.get("retry_count", 1)
            details["queue_channel"] = "gateway_settlement_retry"

        elif action.action_type == ActionType.MARK_FOR_REVIEW:
            side_effects.append("CASE_ROUTED_TO_CONTROLLER_REVIEW_QUEUE")
            details["queue_priority"] = action.payload.get("priority", "MEDIUM")

        elif action.action_type == ActionType.ESCALATE:
            side_effects.append("CASE_ESCALATED_TO_SENIOR_FINANCE_OPERATIONS")
            details["escalation_tier"] = "TIER_2_FINANCE_OPS"

        elif action.action_type == ActionType.REQUEST_MANUAL_VERIFICATION:
            side_effects.append("MANUAL_DOCUMENT_VERIFICATION_REQUESTED")
            details["document_types_required"] = ["bank_statement", "acquirer_batch_receipt"]

        return side_effects, details
