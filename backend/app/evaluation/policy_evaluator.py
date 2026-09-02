"""
Policy and Controlled Action Evaluation Harness.

Computes 8+ objective metrics assessing policy correctness, safety gating,
unauthorized action rejection, idempotency, and verifier gating.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.action import (
    ActionState,
    ActionType,
    AuthorizationStatus,
    UnauthorizedExecutionError,
)
from app.domain.enums import ExceptionType
from app.domain.investigation import (
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecisionOutcome,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.policy.executor import SimulationActionExecutor
from app.policy.policy_engine import DeterministicPolicyEngine
from app.services.policy_service import PolicyService


class PolicyEvaluationMetrics(BaseModel):
    """Metrics assessing policy evaluation and action governance quality."""

    model_config = ConfigDict(frozen=True)

    total_cases_evaluated: int = Field(description="Total cases passed through policy evaluation")
    policy_correctness_rate: float = Field(
        description="Percentage of decisions matching expected policy outcome"
    )
    unauthorized_rejection_rate: float = Field(
        description="Percentage of unauthorized actions rejected by executor (100% required)"
    )
    duplicate_prevention_rate: float = Field(
        description="Percentage of duplicate actions handled idempotently (100% required)"
    )
    safe_fallback_rate: float = Field(
        description="Percentage of unknown policies safely failing closed (100% required)"
    )
    verifier_gated_rate: float = Field(
        description="Percentage of unverified AI investigations blocked from auto-action"
    )
    deterministic_truth_preservation_rate: float = Field(
        description="Percentage of actions preserving deterministic truth (100% required)"
    )
    simulated_execution_success_rate: float = Field(
        description="Percentage of authorized actions executed successfully in simulation"
    )
    avg_policy_latency_ms: float = Field(
        description="Average latency for policy decision evaluation in ms"
    )
    avg_execution_latency_ms: float = Field(
        description="Average latency for action execution in ms"
    )


@dataclass
class PolicyTestCase:
    """Individual test scenario for policy and action evaluation."""

    case_id: str
    scenario_name: str
    deterministic_result: ReconciliationResult
    envelope: VerifiedInvestigationEnvelope | None
    policy_config: DomainPolicyConfig | None
    requested_action: ActionType | None
    expected_decision: PolicyDecisionOutcome
    expected_autonomous_authorized: bool
    should_test_unauthorized_execution: bool = False
    should_test_duplicate: bool = False
    retry_count: int = 0


class PolicyEvaluator:
    """
    Harness evaluating Policy Engine and Controlled Action outcomes across benchmarks.
    """

    def __init__(self, policy_service: PolicyService | None = None) -> None:
        self.policy_service = policy_service or PolicyService(
            policy_engine=DeterministicPolicyEngine(),
            executor=SimulationActionExecutor(),
        )

    async def evaluate_scenarios(
        self, test_cases: list[PolicyTestCase]
    ) -> tuple[PolicyEvaluationMetrics, list[dict[str, Any]]]:
        """
        Execute full policy evaluation and action lifecycle across all test scenarios.
        """
        total = len(test_cases)
        correct_decisions = 0
        unauthorized_rejections_tested = 0
        unauthorized_rejections_passed = 0
        duplicates_tested = 0
        duplicates_passed = 0
        unknown_policy_tested = 0
        unknown_policy_passed = 0
        verifier_gated_tested = 0
        verifier_gated_passed = 0
        truth_preservations_passed = 0
        authorized_executions_tested = 0
        authorized_executions_passed = 0

        total_policy_latency = 0.0
        total_exec_latency = 0.0
        case_reports: list[dict[str, Any]] = []

        for tc in test_cases:
            # 1. Authorize Action
            import time

            p_start = time.perf_counter()
            action, decision, audit_events = await self.policy_service.authorize_action(
                case_id=tc.case_id,
                deterministic_result=tc.deterministic_result,
                envelope=tc.envelope,
                policy_config=tc.policy_config,
                requested_action=tc.requested_action,
                retry_count=tc.retry_count,
            )
            p_latency = (time.perf_counter() - p_start) * 1000.0
            total_policy_latency += p_latency

            # Check decision correctness
            if (
                decision.decision == tc.expected_decision
                and decision.is_autonomous_authorized == tc.expected_autonomous_authorized
            ):
                correct_decisions += 1

            # Check deterministic truth preservation
            det_class = tc.deterministic_result.classification
            if action.action_type == ActionType.AUTO_RECONCILE and det_class in (
                ExceptionType.CURRENCY_MISMATCH,
                ExceptionType.DUPLICATE_RECORD,
                ExceptionType.MISSING_SETTLEMENT,
            ):
                if action.authorization_status == AuthorizationStatus.DENIED:
                    truth_preservations_passed += 1
            else:
                truth_preservations_passed += 1

            # Check unknown policy safe fallback
            if (
                tc.policy_config is not None
                and tc.policy_config.fee_tax_policy is None
                and not tc.deterministic_result.evidence.monetary.is_fee_policy_known
                and det_class != ExceptionType.EXACT_MATCH
            ):
                unknown_policy_tested += 1
                if decision.decision in (PolicyDecisionOutcome.DENY, PolicyDecisionOutcome.REVIEW):
                    unknown_policy_passed += 1

            # Check verifier gating
            if (
                tc.envelope is not None
                and tc.envelope.verification.verifier_status != VerifierStatus.VERIFIED
            ):
                verifier_gated_tested += 1
                if (
                    not decision.is_autonomous_authorized
                    or action.authorization_status == AuthorizationStatus.DENIED
                ):
                    verifier_gated_passed += 1

            # 2. Test Execution
            e_latency = 0.0
            exec_status = "NOT_EXECUTED"

            if action.authorization_status == AuthorizationStatus.AUTHORIZED:
                authorized_executions_tested += 1
                e_start = time.perf_counter()
                exec_action, result, exec_events = await self.policy_service.execute_action(action)
                e_latency = (time.perf_counter() - e_start) * 1000.0
                total_exec_latency += e_latency

                if (
                    exec_action.state == ActionState.EXECUTED
                    and result.status == ActionState.EXECUTED
                ):
                    authorized_executions_passed += 1
                    exec_status = "EXECUTED"

                # Check Idempotency
                if tc.should_test_duplicate:
                    duplicates_tested += 1
                    dup_action, dup_result, _ = await self.policy_service.execute_action(action)
                    if (
                        dup_result.action_id == result.action_id
                        and dup_action.state == ActionState.EXECUTED
                    ):
                        duplicates_passed += 1

            # 3. Test Unauthorized Execution Rejection
            if (
                tc.should_test_unauthorized_execution
                or action.authorization_status != AuthorizationStatus.AUTHORIZED
            ):
                unauthorized_rejections_tested += 1
                # Attempt to directly execute an unauthorized action
                try:
                    await self.policy_service.execute_action(action)
                    # If this succeeds on unauthorized action, it's a failure!
                except UnauthorizedExecutionError:
                    unauthorized_rejections_passed += 1

            case_reports.append(
                {
                    "case_id": tc.case_id,
                    "scenario": tc.scenario_name,
                    "requested_action": action.action_type.value,
                    "decision": decision.decision.value,
                    "is_authorized": decision.is_autonomous_authorized,
                    "reasons": decision.reason_codes,
                    "execution_status": exec_status,
                    "policy_latency_ms": round(p_latency, 2),
                }
            )

        metrics = PolicyEvaluationMetrics(
            total_cases_evaluated=total,
            policy_correctness_rate=round(correct_decisions / max(total, 1), 4),
            unauthorized_rejection_rate=round(
                unauthorized_rejections_passed / max(unauthorized_rejections_tested, 1), 4
            ),
            duplicate_prevention_rate=round(
                duplicates_passed
                / max(duplicates_passed if duplicates_tested == 0 else duplicates_tested, 1),
                4,
            ),
            safe_fallback_rate=round(unknown_policy_passed / max(unknown_policy_tested, 1), 4),
            verifier_gated_rate=round(verifier_gated_passed / max(verifier_gated_tested, 1), 4),
            deterministic_truth_preservation_rate=round(
                truth_preservations_passed / max(total, 1), 4
            ),
            simulated_execution_success_rate=round(
                authorized_executions_passed / max(authorized_executions_tested, 1), 4
            ),
            avg_policy_latency_ms=round(total_policy_latency / max(total, 1), 2),
            avg_execution_latency_ms=round(
                total_exec_latency / max(authorized_executions_tested, 1), 2
            ),
        )

        return metrics, case_reports
