"""Immutable reconciliation result models for single cases and batch operations."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import ReconciliationEvidence


class ReconciliationResult(BaseModel):
    """Immutable, authoritative reconciliation decision for a single candidate case."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(description="Unique reconciliation case identifier")
    order_id: str = Field(description="Associated merchant order reference")
    classification: ExceptionType = Field(
        description="Deterministic exception classification or EXACT_MATCH"
    )
    policy_outcome: PolicyOutcome = Field(
        description="Policy gate decision: AUTO_RECONCILE, REVIEW_REQUIRED, or UNRESOLVED"
    )
    confidence: float = Field(
        default=1.0, description="Calibrated confidence score (1.0 for deterministic rule matches)"
    )
    payment_id: str | None = Field(default=None, description="Matched payment ID")
    settlement_ids: list[str] = Field(
        default_factory=list, description="Matched settlement payout IDs"
    )
    ledger_ids: list[str] = Field(
        default_factory=list, description="Matched ledger journal entry IDs"
    )
    evidence: ReconciliationEvidence = Field(
        description="Complete structured multi-source financial evidence"
    )
    reason_code: str = Field(
        description="Machine-readable rule reason code explaining classification"
    )
    summary: str = Field(
        description="Concise, factual human-readable summary of reconciliation findings"
    )
    reconciled_at: str = Field(
        description="UTC ISO 8601 timestamp of reconciliation engine execution"
    )


class BatchPerformanceMetrics(BaseModel):
    """Execution performance metrics for a batch reconciliation run."""

    model_config = ConfigDict(frozen=True)

    total_records_processed: int = Field(description="Total raw records evaluated")
    total_cases_reconciled: int = Field(description="Total candidate groups processed")
    candidate_generation_time_ms: float = Field(description="Time spent indexing and grouping (ms)")
    evidence_and_classification_time_ms: float = Field(
        description="Time spent evaluating evidence and classifying (ms)"
    )
    total_wall_clock_time_ms: float = Field(description="Total batch processing latency (ms)")
    throughput_records_per_sec: float = Field(description="Processing throughput in records/sec")
    latency_p50_ms: float = Field(description="P50 latency per case in milliseconds")
    latency_p95_ms: float = Field(description="P95 latency per case in milliseconds")
    latency_p99_ms: float = Field(description="P99 latency per case in milliseconds")


class BatchReconciliationResult(BaseModel):
    """Encapsulates the complete result of a batch reconciliation run."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str = Field(description="Dataset identifier processed")
    engine_version: str = Field(default="2.0.0", description="Reconciliation engine version")
    total_cases: int = Field(description="Total reconciliation cases produced")
    results: list[ReconciliationResult] = Field(
        description="List of individual reconciliation case results"
    )
    class_distribution: dict[str, int] = Field(
        description="Count of cases classified per ExceptionType"
    )
    policy_distribution: dict[str, int] = Field(
        description="Count of cases categorized per PolicyOutcome"
    )
    performance_metrics: BatchPerformanceMetrics = Field(
        description="Processing throughput and latency profiles"
    )
