"""
Policy Service.

Coordinates policy evaluation, action authorization, and controlled execution.

Strict Non-Negotiable Rules:
1. The Policy Engine authorizes; the Action Executor executes.
2. AI recommendations are inputs; deterministic policy gates decide outcomes.
3. Every state change emits an immutable audit event.
"""

from __future__ import annotations

from typing import Any

from app.domain.action import (
    ActionPreconditions,
    ActionResult,
    ActionState,
    ActionType,
    AuthorizationStatus,
    ControlledAction,
)
from app.domain.audit import AuditEvent, AuditEventType
from app.domain.investigation import VerifiedInvestigationEnvelope
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecision,
    PolicyDecisionOutcome,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.policy.executor import ActionExecutor, SimulationActionExecutor
from app.policy.policy_engine import DeterministicPolicyEngine


class PolicyService:
    """
    Service managing the policy-gated resolution lifecycle.
    """

    def __init__(
        self,
        policy_engine: DeterministicPolicyEngine | None = None,
        executor: ActionExecutor | None = None,
    ) -> None:
        self.policy_engine = policy_engine or DeterministicPolicyEngine()
        self.executor = executor or SimulationActionExecutor()

    def evaluate_case_policy(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        envelope: VerifiedInvestigationEnvelope | None = None,
        policy_config: DomainPolicyConfig | None = None,
        requested_action: ActionType | None = None,
        retry_count: int = 0,
    ) -> tuple[PolicyDecision, ActionPreconditions]:
        """
        Evaluate policy authorization for a case without mutating state.
        """
        return self.policy_engine.evaluate_action_authorization(
            case_id=case_id,
            deterministic_result=deterministic_result,
            envelope=envelope,
            policy_config=policy_config,
            requested_action=requested_action,
            retry_count=retry_count,
        )

    async def authorize_action(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        envelope: VerifiedInvestigationEnvelope | None = None,
        policy_config: DomainPolicyConfig | None = None,
        requested_action: ActionType | None = None,
        payload: dict[str, Any] | None = None,
        requested_by: str = "policy_service",
        retry_count: int = 0,
    ) -> tuple[ControlledAction, PolicyDecision, list[AuditEvent]]:
        """
        Evaluate policy, construct a ControlledAction, and transition to AUTHORIZED or REJECTED.
        """
        config = policy_config or DomainPolicyConfig()
        action_type = requested_action or self.policy_engine._infer_default_action(
            deterministic_result, envelope
        )

        decision, preconditions = self.policy_engine.evaluate_action_authorization(
            case_id=case_id,
            deterministic_result=deterministic_result,
            envelope=envelope,
            policy_config=config,
            requested_action=action_type,
            retry_count=retry_count,
        )

        evidence_refs = envelope.investigation.evidence_references if envelope is not None else []

        idempotency_key = ControlledAction.generate_idempotency_key(
            case_id=case_id,
            action_type=action_type,
            payload=payload,
            policy_version=config.policy_version,
        )

        # 1. Create Initial REQUESTED Action
        action = ControlledAction(
            case_id=case_id,
            action_type=action_type,
            state=ActionState.REQUESTED,
            authorization_status=AuthorizationStatus.PENDING_REVIEW,
            idempotency_key=idempotency_key,
            policy_version=config.policy_version,
            preconditions=preconditions,
            evidence_references=evidence_refs,
            payload=payload or {},
            requested_by=requested_by,
        )

        audit_events: list[AuditEvent] = [
            AuditEvent(
                event_type=AuditEventType.ACTION_REQUESTED,
                case_id=case_id,
                action_id=action.action_id,
                policy_version=config.policy_version,
                evidence_references=evidence_refs,
                payload={"action_type": action_type.value},
            )
        ]

        # 2. Transition to VALIDATING
        action = action.transition_to(ActionState.VALIDATING)

        # 3. Transition to AUTHORIZED or REJECTED based on PolicyDecision
        if decision.decision == PolicyDecisionOutcome.ALLOW and decision.is_autonomous_authorized:
            action = action.transition_to(
                ActionState.AUTHORIZED,
                authorization_status=AuthorizationStatus.AUTHORIZED,
            )
            audit_events.append(
                AuditEvent(
                    event_type=AuditEventType.ACTION_AUTHORIZED,
                    case_id=case_id,
                    action_id=action.action_id,
                    policy_version=config.policy_version,
                    evidence_references=evidence_refs,
                    payload={"decision": decision.model_dump()},
                )
            )
        else:
            action = action.transition_to(
                ActionState.REJECTED,
                authorization_status=AuthorizationStatus.DENIED,
                rejection_reasons=decision.rejection_reasons,
            )
            audit_events.append(
                AuditEvent(
                    event_type=AuditEventType.ACTION_REJECTED,
                    case_id=case_id,
                    action_id=action.action_id,
                    policy_version=config.policy_version,
                    evidence_references=evidence_refs,
                    payload={
                        "decision": decision.model_dump(),
                        "reasons": decision.rejection_reasons,
                    },
                )
            )

        return action, decision, audit_events

    async def execute_action(
        self, action: ControlledAction
    ) -> tuple[ControlledAction, ActionResult, list[AuditEvent]]:
        """
        Execute an authorized action using the configured ActionExecutor.
        """
        return await self.executor.execute_action(action)
