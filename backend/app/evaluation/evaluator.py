"""
Independent evaluation harness computing accuracy, macro-F1, per-class metrics,
and confusion matrix.
"""

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType
from app.domain.ground_truth import GroundTruthRecord
from app.domain.reconciliation_result import BatchPerformanceMetrics, ReconciliationResult
from app.domain.sanitization import validate_dataset_id
from app.domain.time import to_iso_utc


class ClassMetric(BaseModel):
    """Precision, Recall, F1, and support for an individual exception class."""

    model_config = ConfigDict(frozen=True)

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    support: int


class FailureDetail(BaseModel):
    """Detailed diagnosis of an individual misclassified reconciliation case."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    order_id: str
    actual_class: str
    predicted_class: str
    reason_code: str
    summary: str
    discrepancy_flags: list[str]
    failure_reason: str


class BenchmarkEvaluationReport(BaseModel):
    """Complete, machine-readable evaluation report against isolated ground truth."""

    model_config = ConfigDict(frozen=True)

    benchmark_id: str
    dataset_id: str
    timestamp: str
    total_records: int
    correct_classifications: int
    overall_accuracy: float
    macro_f1: float
    false_match_rate: float = Field(
        description="Rate of true exceptions incorrectly classified as EXACT_MATCH (Target: 0.0)"
    )
    false_unresolved_rate: float = Field(
        description="Rate of clean records incorrectly categorized as UNRESOLVED"
    )
    per_class_metrics: dict[str, ClassMetric]
    confusion_matrix: dict[str, dict[str, int]]
    failures: list[FailureDetail]
    performance_metrics: BatchPerformanceMetrics | None = None


def _find_ground_truth_root() -> Path:
    candidates = [
        Path.cwd() / "data" / "ground_truth",
        Path.cwd().parent / "data" / "ground_truth",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "ground_truth",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class BenchmarkEvaluator:
    """
    Independent ground-truth evaluator.

    Accesses ground truth only within evaluation context; completely separated from inference logic.
    """

    def evaluate(
        self,
        results: list[ReconciliationResult],
        ground_truth: list[GroundTruthRecord],
        dataset_id: str,
        performance_metrics: BatchPerformanceMetrics | None = None,
    ) -> BenchmarkEvaluationReport:
        """
        Compare actual reconciliation results against ground truth.
        """
        # Map ground truth by order_id
        gt_by_order: dict[str, GroundTruthRecord] = {gt.order_id: gt for gt in ground_truth}

        all_classes = [c.value for c in ExceptionType]
        confusion_matrix: dict[str, dict[str, int]] = {
            act: {pred: 0 for pred in all_classes} for act in all_classes
        }

        tp_counts: dict[str, int] = defaultdict(int)
        fp_counts: dict[str, int] = defaultdict(int)
        fn_counts: dict[str, int] = defaultdict(int)
        support_counts: dict[str, int] = defaultdict(int)

        correct_count = 0
        failures: list[FailureDetail] = []

        for res in results:
            gt = gt_by_order.get(res.order_id)
            if not gt:
                continue

            actual = gt.expected_classification.value
            predicted = res.classification.value

            confusion_matrix[actual][predicted] += 1
            support_counts[actual] += 1

            if actual == predicted:
                correct_count += 1
                tp_counts[actual] += 1
            else:
                fp_counts[predicted] += 1
                fn_counts[actual] += 1
                failures.append(
                    FailureDetail(
                        case_id=res.case_id,
                        order_id=res.order_id,
                        actual_class=actual,
                        predicted_class=predicted,
                        reason_code=res.reason_code,
                        summary=res.summary,
                        discrepancy_flags=res.evidence.flags,
                        failure_reason=(
                            f"Expected {actual} but predicted {predicted} "
                            f"via rule {res.reason_code}"
                        ),
                    )
                )

        total_evaluated = len(results)
        accuracy = (correct_count / total_evaluated) if total_evaluated > 0 else 0.0

        # Compute per-class Precision, Recall, F1
        per_class_metrics: dict[str, ClassMetric] = {}
        f1_sum = 0.0

        for c_val in all_classes:
            tp = tp_counts[c_val]
            fp = fp_counts[c_val]
            fn = fn_counts[c_val]
            supp = support_counts[c_val]

            prec = (tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if supp == 0 and fp == 0 else 0.0)
            rec = (tp / (tp + fn)) if (tp + fn) > 0 else (1.0 if supp == 0 else 0.0)
            f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

            f1_sum += f1
            per_class_metrics[c_val] = ClassMetric(
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1_score=round(f1, 4),
                support=supp,
            )

        macro_f1 = f1_sum / len(all_classes) if all_classes else 0.0

        # False Match Rate: actual != EXACT_MATCH but predicted == EXACT_MATCH
        total_exceptions = sum(
            support_counts[c] for c in all_classes if c != ExceptionType.EXACT_MATCH.value
        )
        false_matches = sum(
            confusion_matrix[act][ExceptionType.EXACT_MATCH.value]
            for act in all_classes
            if act != ExceptionType.EXACT_MATCH.value
        )
        fmr = (false_matches / total_exceptions) if total_exceptions > 0 else 0.0

        # False Unresolved Rate: actual == EXACT_MATCH but predicted policy == UNRESOLVED
        clean_total = support_counts[ExceptionType.EXACT_MATCH.value]
        false_unresolved = 0
        for res in results:
            gt = gt_by_order.get(res.order_id)
            if (
                gt
                and gt.expected_classification == ExceptionType.EXACT_MATCH
                and res.policy_outcome.value == "UNRESOLVED"
            ):
                false_unresolved += 1
        fur = (false_unresolved / clean_total) if clean_total > 0 else 0.0

        now_str = to_iso_utc(datetime.now(UTC))
        benchmark_id = f"bench_{dataset_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        return BenchmarkEvaluationReport(
            benchmark_id=benchmark_id,
            dataset_id=dataset_id,
            timestamp=now_str,
            total_records=total_evaluated,
            correct_classifications=correct_count,
            overall_accuracy=round(accuracy, 4),
            macro_f1=round(macro_f1, 4),
            false_match_rate=round(fmr, 4),
            false_unresolved_rate=round(fur, 4),
            per_class_metrics=per_class_metrics,
            confusion_matrix=confusion_matrix,
            failures=failures,
            performance_metrics=performance_metrics,
        )

    def evaluate_from_disk(
        self,
        dataset_id: str,
        results: list[ReconciliationResult],
        base_dir: str | Path | None = None,
        performance_metrics: BatchPerformanceMetrics | None = None,
    ) -> BenchmarkEvaluationReport:
        """
        Load isolated ground truth from disk and evaluate.
        """
        valid_id = validate_dataset_id(dataset_id)
        root = Path(base_dir) if base_dir else _find_ground_truth_root()
        gt_file = root / valid_id / "ground_truth.json"

        if not gt_file.exists():
            raise FileNotFoundError(f"Ground truth file not found: {gt_file}")

        with open(gt_file, encoding="utf-8") as f:
            raw_gt = json.load(f)

        ground_truth = [GroundTruthRecord.model_validate(rec) for rec in raw_gt]
        return self.evaluate(
            results=results,
            ground_truth=ground_truth,
            dataset_id=valid_id,
            performance_metrics=performance_metrics,
        )
