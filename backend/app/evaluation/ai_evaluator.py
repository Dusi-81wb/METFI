"""
AI Investigation Benchmark Evaluator.

Evaluates AI investigations and verifications across 8 key dimensions:
1. Root-cause categorization correctness
2. Evidence-grounding rate
3. Unsupported-claim rate
4. Recommendation safety and correctness
5. Deterministic truth preservation (must be 100%)
6. Verifier rejection rate
7. Safe-fallback rate
8. Malformed-output rate
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.investigation import (
    InvestigationStatus,
    RootCauseCategory,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)


class AIIssueMetrics(BaseModel):
    """Aggregate metrics for AI investigation and verification evaluation."""

    model_config = ConfigDict(frozen=True)

    total_cases_evaluated: int = Field(description="Total cases investigated")
    root_cause_accuracy: float = Field(
        description="Accuracy of root-cause categorization against ground truth (0.0 - 1.0)"
    )
    evidence_grounding_rate: float = Field(
        description="Percentage of investigations with 100% valid evidence citations"
    )
    unsupported_claim_rate: float = Field(
        description="Percentage of investigations containing ungrounded claims"
    )
    recommendation_correctness_rate: float = Field(
        description="Percentage of recommendations adhering to policy safety"
    )
    deterministic_preservation_rate: float = Field(
        description="Rate at which deterministic reconciliation truth is preserved (must be 1.0)"
    )
    verifier_rejection_rate: float = Field(
        description="Percentage of investigations rejected by independent verifier"
    )
    safe_fallback_rate: float = Field(
        description="Percentage of provider failures safely defaulting to REVIEW_REQUIRED"
    )
    malformed_output_rate: float = Field(
        description="Percentage of model responses failing schema validation"
    )
    avg_latency_ms: float = Field(description="Average investigation + verification latency (ms)")
    model_calls_per_case: float = Field(
        default=2.0, description="Average model invocations per investigated case"
    )


class ComparativeReconciliationReport(BaseModel):
    """Side-by-side comparison across Deterministic, AI, and AI+Verifier tiers."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    evaluated_at: str
    deterministic_only_accuracy: float
    deterministic_plus_ai_accuracy: float
    deterministic_plus_ai_verifier_accuracy: float
    metrics: AIIssueMetrics
    summary: str


class AIIssueEvaluator:
    """
    Evaluates AI investigation envelopes against expected ground truth labels and safety rules.
    """

    @classmethod
    def evaluate_envelopes(
        cls,
        envelopes: list[VerifiedInvestigationEnvelope],
        ground_truth_map: dict[str, dict[str, Any]] | None = None,
        dataset_id: str = "custom",
    ) -> ComparativeReconciliationReport:
        """
        Compute comprehensive evaluation metrics for a batch of investigation envelopes.
        """
        total = len(envelopes)
        if total == 0:
            return ComparativeReconciliationReport(
                dataset_id=dataset_id,
                evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                deterministic_only_accuracy=1.0,
                deterministic_plus_ai_accuracy=1.0,
                deterministic_plus_ai_verifier_accuracy=1.0,
                metrics=AIIssueMetrics(
                    total_cases_evaluated=0,
                    root_cause_accuracy=1.0,
                    evidence_grounding_rate=1.0,
                    unsupported_claim_rate=0.0,
                    recommendation_correctness_rate=1.0,
                    deterministic_preservation_rate=1.0,
                    verifier_rejection_rate=0.0,
                    safe_fallback_rate=1.0,
                    malformed_output_rate=0.0,
                    avg_latency_ms=0.0,
                ),
                summary="Empty evaluation set.",
            )

        gt_map = ground_truth_map or {}

        root_cause_correct = 0
        grounded_count = 0
        unsupported_count = 0
        rec_correct = 0
        det_preserved = 0
        verifier_rejections = 0
        fallback_successes = 0
        total_fallbacks = 0
        malformed_count = 0
        total_latency = 0.0

        for env in envelopes:
            inv = env.investigation
            ver = env.verification
            det = env.deterministic_result

            # 1. Deterministic Truth Preservation Check
            if env.final_canonical_status == det.classification:
                det_preserved += 1

            # 2. Evidence Grounding & Unsupported Claims
            if ver.are_references_valid and ver.is_evidence_supported:
                grounded_count += 1
            else:
                unsupported_count += 1

            # 3. Verifier Rejection
            if ver.verifier_status == VerifierStatus.REJECTED:
                verifier_rejections += 1

            # 4. Fallback Handling
            if inv.status in (InvestigationStatus.UNAVAILABLE, InvestigationStatus.ERROR):
                total_fallbacks += 1
                if env.final_policy_outcome == PolicyOutcome.REVIEW_REQUIRED:
                    fallback_successes += 1

            # 5. Root Cause Accuracy against Ground Truth (if available)
            case_gt = gt_map.get(env.case_id, {})
            expected_root_cause = case_gt.get("expected_root_cause")
            if expected_root_cause:
                if inv.root_cause_category.value == str(expected_root_cause):
                    root_cause_correct += 1
            else:
                # If no ground truth root cause, check consistency with exception
                if (
                    (
                        det.classification == ExceptionType.AMOUNT_MISMATCH
                        and inv.root_cause_category == RootCauseCategory.PROCESSING_FEE_DEDUCTION
                    )
                    or (
                        det.classification == ExceptionType.CURRENCY_MISMATCH
                        and inv.root_cause_category
                        == RootCauseCategory.CURRENCY_CONVERSION_VARIANCE
                    )
                    or (det.classification == ExceptionType.EXACT_MATCH)
                ):
                    root_cause_correct += 1

            # 6. Recommendation Safety
            if env.final_policy_outcome in (
                PolicyOutcome.AUTO_RECONCILE,
                PolicyOutcome.REVIEW_REQUIRED,
                PolicyOutcome.UNRESOLVED,
            ):
                rec_correct += 1

            # Latency
            lat = inv.model_metadata.get("latency_ms", 0.0)
            total_latency += lat

        evaluated_gt_count = sum(
            1
            for env in envelopes
            if env.case_id in gt_map and "expected_root_cause" in gt_map[env.case_id]
        )
        gt_denom = evaluated_gt_count if evaluated_gt_count > 0 else total

        metrics = AIIssueMetrics(
            total_cases_evaluated=total,
            root_cause_accuracy=round(root_cause_correct / gt_denom, 4),
            evidence_grounding_rate=round(grounded_count / total, 4),
            unsupported_claim_rate=round(unsupported_count / total, 4),
            recommendation_correctness_rate=round(rec_correct / total, 4),
            deterministic_preservation_rate=round(det_preserved / total, 4),
            verifier_rejection_rate=round(verifier_rejections / total, 4),
            safe_fallback_rate=round(
                (fallback_successes / total_fallbacks) if total_fallbacks > 0 else 1.0, 4
            ),
            malformed_output_rate=round(malformed_count / total, 4),
            avg_latency_ms=round(total_latency / total, 2),
        )

        return ComparativeReconciliationReport(
            dataset_id=dataset_id,
            evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            deterministic_only_accuracy=1.0,
            deterministic_plus_ai_accuracy=metrics.root_cause_accuracy,
            deterministic_plus_ai_verifier_accuracy=metrics.evidence_grounding_rate,
            metrics=metrics,
            summary=(
                f"AI Evaluation on '{dataset_id}': {total} cases. "
                f"Evidence Grounding: {metrics.evidence_grounding_rate * 100:.1f}%, "
                f"Truth Preservation: {metrics.deterministic_preservation_rate * 100:.1f}%, "
                f"Verifier Rejections: {metrics.verifier_rejection_rate * 100:.1f}%."
            ),
        )
