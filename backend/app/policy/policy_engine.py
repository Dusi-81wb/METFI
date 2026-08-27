"""Deterministic policy engine mapping reconciliation findings to operational policy outcomes."""

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import ReconciliationEvidence


class DeterministicPolicyEngine:
    """
    Evaluates reconciliation classifications and evidence against corporate finance policy gates.
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
        Map exception classification to authorized policy outcome.

        Guarantees:
        - AUTO_RECONCILE is strictly forbidden for any exception containing anomalies.
        - High-risk or incomplete evidence defaults safely to UNRESOLVED.
        """
        # Hard invariant: AUTO_RECONCILE requires clean EXACT_MATCH
        if classification != ExceptionType.EXACT_MATCH:
            outcome = self.POLICY_MAPPING.get(classification, PolicyOutcome.UNRESOLVED)
            if outcome == PolicyOutcome.AUTO_RECONCILE:
                return PolicyOutcome.REVIEW_REQUIRED
            return outcome

        # If classified as EXACT_MATCH, verify no discrepancy flags exist
        if evidence.flags:
            return PolicyOutcome.REVIEW_REQUIRED

        return PolicyOutcome.AUTO_RECONCILE
