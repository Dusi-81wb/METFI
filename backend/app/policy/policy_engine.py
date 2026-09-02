"""
Deterministic Policy Engine.

Enforces corporate financial control rules, authorization gates, and variance tolerances
over deterministic reconciliation findings and verified AI investigations.

Strict Non-Negotiable Rules:
1. Authority Hierarchy: Deterministic Truth > Policy Engine > AI Recommendation > Action Executor.
2. The Policy Engine is purely deterministic: Same inputs => Same decision.
3. Unknown or missing policies fail closed (REVIEW / UNRESOLVED).
4. AI recommendations are inputs to policy evaluation, not authorization authorities.
5. No action may be authorized if it contradicts canonical deterministic truth.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.action import ActionPreconditions, ActionType
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import ReconciliationEvidence
from app.domain.investigation import (
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.policy import (
    DomainPolicyConfig,
    PolicyDecision,
    PolicyDecisionOutcome,
)
from app.domain.reconciliation_result import ReconciliationResult


class DeterministicPolicyEngine:
    """
    Corporate financial policy engine evaluating reconciliation and investigation states
    against explicit corporate governance rules.
    """

    POLICY_MAPPING: dict[ExceptionType, PolicyOutcome] = {
        ExceptionType.EXACT_MATCH: PolicyOutcome.AUTO_RECONCILE,
        ExceptionType.AMOUNT_MISMATCH: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.DUPLICATE_RECORD: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.DATE_MISMATCH: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.REFERENCE_MISMATCH: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.PARTIAL_SETTLEMENT: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.FEE_DISCREPANCY: PolicyOutcome.REVIEW_REQUIRED,
        ExceptionType.MISSING_SETTLEMENT: PolicyOutcome.UNRESOLVED,
        ExceptionType.CURRENCY_MISMATCH: PolicyOutcome.UNRESOLVED,
        ExceptionType.AMBIGUOUS: PolicyOutcome.UNRESOLVED,
    }

    def evaluate_policy(
        self,
        classification: ExceptionType,
        evidence: ReconciliationEvidence,
    ) -> PolicyOutcome:
        """
        Legacy policy outcome mapping preserving compatibility with Phase 2/3.
        """
        if classification != ExceptionType.EXACT_MATCH:
            outcome = self.POLICY_MAPPING.get(classification, PolicyOutcome.UNRESOLVED)
            if outcome == PolicyOutcome.AUTO_RECONCILE:
                return PolicyOutcome.REVIEW_REQUIRED
            return outcome

        if evidence.flags:
            return PolicyOutcome.REVIEW_REQUIRED

        return PolicyOutcome.AUTO_RECONCILE

    def evaluate_action_authorization(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        envelope: VerifiedInvestigationEnvelope | None = None,
        policy_config: DomainPolicyConfig | None = None,
        requested_action: ActionType | None = None,
        retry_count: int = 0,
    ) -> tuple[PolicyDecision, ActionPreconditions]:
        """
        Evaluate full multi-input policy authorization for a proposed controlled action.

        Returns:
            tuple[PolicyDecision, ActionPreconditions]
        """
        config = policy_config or DomainPolicyConfig()
        action = requested_action or self._infer_default_action(deterministic_result, envelope)

        reason_codes: list[str] = []
        rejection_reasons: list[str] = []
        applicable_rules: list[str] = []

        is_truth_preserved = True
        is_verifier_passed = True
        is_evidence_complete = True
        is_within_variance = True
        is_within_retry = True
        is_policy_known = True
        has_idempotency = True

        m = deterministic_result.evidence.monetary
        det_class = deterministic_result.classification

        # -------------------------------------------------------------------------
        # GATE 1: Deterministic Primacy & Blocking Conflict Check
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_DETERMINISTIC_PRIMACY")
        if action == ActionType.AUTO_RECONCILE:
            if det_class in (
                ExceptionType.CURRENCY_MISMATCH,
                ExceptionType.DUPLICATE_RECORD,
                ExceptionType.MISSING_SETTLEMENT,
                ExceptionType.AMBIGUOUS,
            ):
                is_truth_preserved = False
                msg = f"Action AUTO_RECONCILE contradicts classification {det_class.value}."
                rejection_reasons.append(msg)
                reason_codes.append("ERR_BLOCKING_CLASSIFICATION_CONFLICT")

        # -------------------------------------------------------------------------
        # GATE 2: AI Verifier Gating
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_VERIFIER_GATING")
        if envelope is not None:
            v_res = envelope.verification
            if v_res.verifier_status != VerifierStatus.VERIFIED:
                is_verifier_passed = False
                if action in (ActionType.AUTO_RECONCILE, ActionType.REQUEST_RETRY):
                    v_msg = (
                        f"Action {action.value} denied: Verifier "
                        f"{v_res.verifier_status.value} ({v_res.verifier_notes})."
                    )
                    rejection_reasons.append(v_msg)
                    reason_codes.append("ERR_VERIFIER_NOT_PASSED")

            if not v_res.are_references_valid:
                is_evidence_complete = False
                rejection_reasons.append(
                    "Action contains uncertified or invalid evidence field references."
                )
                reason_codes.append("ERR_INVALID_EVIDENCE_REFERENCES")

        # -------------------------------------------------------------------------
        # GATE 3: Unknown Policy / Closed Fallback Check
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_POLICY_KNOWN_CHECK")
        if action == ActionType.AUTO_RECONCILE and det_class != ExceptionType.EXACT_MATCH:
            if not m.is_fee_policy_known and config.fee_tax_policy is None:
                is_policy_known = False
                rejection_reasons.append(
                    "AUTO_RECONCILE denied: Contract fee/tax policy is unknown / unconfigured."
                )
                reason_codes.append("ERR_UNKNOWN_FEE_POLICY")

        # -------------------------------------------------------------------------
        # GATE 4: Variance Tolerance Limits Check
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_VARIANCE_TOLERANCE")
        if action == ActionType.AUTO_RECONCILE:
            tol = config.variance_tolerance
            abs_fee_var = abs(m.fee_variance)
            abs_tax_var = abs(m.tax_variance)

            if abs_fee_var > tol.max_absolute_fee_variance:
                is_within_variance = False
                rejection_reasons.append(
                    f"Fee variance {abs_fee_var} exceeds limit {tol.max_absolute_fee_variance}."
                )
                reason_codes.append("ERR_FEE_VARIANCE_EXCEEDS_TOLERANCE")

            if abs_tax_var > tol.max_absolute_tax_variance:
                is_within_variance = False
                rejection_reasons.append(
                    f"Tax variance {abs_tax_var} exceeds limit {tol.max_absolute_tax_variance}."
                )
                reason_codes.append("ERR_TAX_VARIANCE_EXCEEDS_TOLERANCE")

        # -------------------------------------------------------------------------
        # GATE 5: Retry Policy Limits Check
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_RETRY_LIMITS")
        if action == ActionType.REQUEST_RETRY:
            if det_class not in config.retry_policy.retryable_exceptions:
                is_within_retry = False
                rejection_reasons.append(
                    f"Classification {det_class.value} is not eligible for automated retry."
                )
                reason_codes.append("ERR_EXCEPTION_NOT_RETRYABLE")

            if retry_count >= config.retry_policy.max_retry_attempts:
                is_within_retry = False
                max_retries = config.retry_policy.max_retry_attempts
                rejection_reasons.append(
                    f"Retry count {retry_count} reached maximum allowed limit ({max_retries})."
                )
                reason_codes.append("ERR_RETRY_LIMIT_EXCEEDED")

        # -------------------------------------------------------------------------
        # GATE 6: Global Auto-Reconcile Master Switch & Cap
        # -------------------------------------------------------------------------
        applicable_rules.append("RULE_TRANSACTION_LIMIT_CAP")
        if action == ActionType.AUTO_RECONCILE:
            if not config.auto_reconciliation_enabled:
                rejection_reasons.append(
                    "AUTO_RECONCILE denied: Global auto-reconciliation master switch is disabled."
                )
                reason_codes.append("ERR_AUTO_RECONCILE_DISABLED")

            gross = m.payment_gross or Decimal("0.00")
            if gross > config.max_auto_reconcile_amount and det_class != ExceptionType.EXACT_MATCH:
                max_cap = config.max_auto_reconcile_amount
                rejection_reasons.append(
                    f"Payment amount {gross} exceeds maximum autonomous cap {max_cap}."
                )
                reason_codes.append("ERR_EXCEEDS_AUTONOMOUS_CAP")

        # Construct Preconditions Checklist
        preconditions = ActionPreconditions(
            is_deterministic_truth_preserved=is_truth_preserved,
            is_verifier_passed=is_verifier_passed,
            is_evidence_complete=is_evidence_complete,
            is_within_variance_tolerance=is_within_variance,
            is_within_retry_limit=is_within_retry,
            is_policy_known=is_policy_known,
            has_valid_idempotency_key=has_idempotency,
        )

        # -------------------------------------------------------------------------
        # Compute Final Authorization Decision
        # -------------------------------------------------------------------------
        if not preconditions.is_all_satisfied() or rejection_reasons:
            decision = PolicyDecisionOutcome.DENY
            is_auth = False
            if action in (ActionType.MARK_FOR_REVIEW, ActionType.ESCALATE):
                # Manual review or escalation requests are permitted even when auto-reconcile fails
                decision = PolicyDecisionOutcome.ALLOW
                is_auth = True
                reason_codes.append("ALLOW_MANUAL_ROUTING")
        else:
            decision = PolicyDecisionOutcome.ALLOW
            is_auth = True
            reason_codes.append(f"ALLOW_{action.value}")

        policy_decision = PolicyDecision(
            decision=decision,
            is_autonomous_authorized=is_auth,
            reason_codes=reason_codes,
            rejection_reasons=rejection_reasons,
            applicable_rules=applicable_rules,
            policy_version=config.policy_version,
            metadata={
                "case_id": case_id,
                "requested_action": action.value,
                "classification": det_class.value,
                "retry_count": retry_count,
            },
        )

        return policy_decision, preconditions

    def _infer_default_action(
        self,
        deterministic_result: ReconciliationResult,
        envelope: VerifiedInvestigationEnvelope | None,
    ) -> ActionType:
        """Infer default action based on deterministic state and verified recommendation."""
        det_class = deterministic_result.classification
        if det_class == ExceptionType.EXACT_MATCH:
            return ActionType.AUTO_RECONCILE

        if (
            envelope is not None
            and envelope.verification.verifier_status == VerifierStatus.VERIFIED
        ):
            rec = envelope.investigation.recommended_action
            if rec.value == ActionType.AUTO_RECONCILE.value:
                return ActionType.AUTO_RECONCILE
            elif rec.value == ActionType.MARK_FOR_REVIEW.value:
                return ActionType.MARK_FOR_REVIEW

        if det_class in (ExceptionType.CURRENCY_MISMATCH, ExceptionType.AMBIGUOUS):
            return ActionType.ESCALATE
        elif det_class == ExceptionType.MISSING_SETTLEMENT:
            return ActionType.REQUEST_RETRY

        return ActionType.MARK_FOR_REVIEW
