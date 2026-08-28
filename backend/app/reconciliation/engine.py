"""
Authoritative deterministic reconciliation engine orchestrating
candidate matching, evidence evaluation, classification, and policy gating.
"""

import time
from collections import defaultdict
from datetime import UTC, datetime

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
    CanonicalTransactionGroup,
)
from app.domain.fee_policy import FeeTaxPolicy, UNSET_POLICY
from app.domain.reconciliation_result import (
    BatchPerformanceMetrics,
    BatchReconciliationResult,
    ReconciliationResult,
)
from app.domain.time import to_iso_utc
from app.policy.policy_engine import DeterministicPolicyEngine
from app.reconciliation.candidate_matcher import CandidateMatcher
from app.reconciliation.classifier import DeterministicClassifier
from app.reconciliation.evidence_extractor import EvidenceExtractor


class DeterministicReconciliationEngine:
    """
    Core Deterministic Financial Reconciliation Engine (Layer D).

    Authoritative financial source of truth. Does not invoke LLMs.
    """

    def __init__(
        self,
        candidate_matcher: CandidateMatcher | None = None,
        evidence_extractor: EvidenceExtractor | None = None,
        classifier: DeterministicClassifier | None = None,
        policy_engine: DeterministicPolicyEngine | None = None,
        default_policy: FeeTaxPolicy | None = None,
    ) -> None:
        self.matcher = candidate_matcher or CandidateMatcher()
        self.extractor = evidence_extractor or EvidenceExtractor()
        self.classifier = classifier or DeterministicClassifier()
        self.policy = policy_engine or DeterministicPolicyEngine()
        self.default_policy = default_policy or FeeTaxPolicy()

    def reconcile_group(
        self,
        group: CanonicalTransactionGroup,
        all_matched_settlements: list[CanonicalSettlement] | None = None,
        policy: FeeTaxPolicy | None | object = UNSET_POLICY,
    ) -> ReconciliationResult:
        """
        Reconcile a single candidate transaction group under specified or default policy.
        """
        active_policy = self.default_policy if policy is UNSET_POLICY else policy
        settlements = (
            all_matched_settlements
            if all_matched_settlements is not None
            else (group.settlements or ([group.settlement] if group.settlement else []))
        )

        evidence = self.extractor.extract_evidence(
            payment=group.payment,
            settlements=settlements,
            ledger_entries=group.ledger_entries,
            policy=active_policy,
            is_ambiguous_candidate=group.is_ambiguous_candidate,
            is_cross_customer_rejected=group.is_cross_customer_rejected,
        )

        classification, reason_code, summary = self.classifier.classify(evidence)
        policy_outcome = self.policy.evaluate_policy(classification, evidence)

        payment_id = group.payment.payment_id if group.payment else None
        settlement_ids = [s.settlement_id for s in settlements]
        ledger_ids = [le.ledger_id for le in group.ledger_entries]

        return ReconciliationResult(
            case_id=group.case_id,
            order_id=group.order_id,
            classification=classification,
            policy_outcome=policy_outcome,
            confidence=1.0,
            payment_id=payment_id,
            settlement_ids=settlement_ids,
            ledger_ids=ledger_ids,
            evidence=evidence,
            reason_code=reason_code,
            summary=summary,
            reconciled_at=to_iso_utc(datetime.now(UTC)),
        )

    def reconcile_batch(
        self,
        payments: list[CanonicalPayment],
        settlements: list[CanonicalSettlement],
        ledger_entries: list[CanonicalLedgerEntry],
        dataset_id: str = "batch",
        policy: FeeTaxPolicy | None | object = UNSET_POLICY,
    ) -> BatchReconciliationResult:
        """
        Execute high-speed deterministic reconciliation across all source feeds.
        """
        start_total = time.perf_counter()
        active_policy = self.default_policy if policy is UNSET_POLICY else policy

        # Step 1: Candidate Generation (Matcher handles exact, fuzzy, and multiplicity linkages)
        start_matcher = time.perf_counter()
        groups = self.matcher.group_candidates(payments, settlements, ledger_entries)
        candidate_time_ms = (time.perf_counter() - start_matcher) * 1000.0

        # Step 2: Evidence Evaluation, Classification, and Policy Mapping
        start_eval = time.perf_counter()
        results: list[ReconciliationResult] = []
        case_latencies_ms: list[float] = []

        for group in groups:
            case_start = time.perf_counter()
            matched_settlements = group.settlements or (
                [group.settlement] if group.settlement else []
            )
            res = self.reconcile_group(
                group=group,
                all_matched_settlements=matched_settlements,
                policy=active_policy,
            )
            results.append(res)
            case_latencies_ms.append((time.perf_counter() - case_start) * 1000.0)

        eval_time_ms = (time.perf_counter() - start_eval) * 1000.0
        total_time_ms = (time.perf_counter() - start_total) * 1000.0

        # Compute distributions
        class_dist: dict[str, int] = defaultdict(int)
        policy_dist: dict[str, int] = defaultdict(int)
        for r in results:
            class_dist[r.classification.value] += 1
            policy_dist[r.policy_outcome.value] += 1

        total_records = len(payments) + len(settlements) + len(ledger_entries)
        throughput = (total_records / (total_time_ms / 1000.0)) if total_time_ms > 0 else 0.0

        # Compute Latency Percentiles
        case_latencies_ms.sort()
        n = len(case_latencies_ms)
        p50 = case_latencies_ms[int(n * 0.50)] if n > 0 else 0.0
        p95 = case_latencies_ms[min(int(n * 0.95), n - 1)] if n > 0 else 0.0
        p99 = case_latencies_ms[min(int(n * 0.99), n - 1)] if n > 0 else 0.0

        metrics = BatchPerformanceMetrics(
            total_records_processed=total_records,
            total_cases_reconciled=len(results),
            candidate_generation_time_ms=candidate_time_ms,
            evidence_and_classification_time_ms=eval_time_ms,
            total_wall_clock_time_ms=total_time_ms,
            throughput_records_per_sec=round(throughput, 2),
            latency_p50_ms=round(p50, 4),
            latency_p95_ms=round(p95, 4),
            latency_p99_ms=round(p99, 4),
        )

        return BatchReconciliationResult(
            dataset_id=dataset_id,
            total_cases=len(results),
            results=results,
            class_distribution=dict(sorted(class_dist.items())),
            policy_distribution=dict(sorted(policy_dist.items())),
            performance_metrics=metrics,
        )
