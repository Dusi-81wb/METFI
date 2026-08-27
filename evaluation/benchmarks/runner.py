"""Benchmark CLI runner executing deterministic reconciliation and evaluation against ground truth."""

import argparse
import json
from pathlib import Path
import sys

# Ensure backend app is on sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.evaluation.evaluator import BenchmarkEvaluator  # noqa: E402
from app.services.reconciliation_service import ReconciliationService  # noqa: E402


def run_benchmark(dataset_id: str, output_path: str | None = None) -> int:
    """Execute end-to-end reconciliation benchmark and write evaluation report."""
    print(f"=== METFI Benchmark Runner ===")
    print(f"Dataset ID : {dataset_id}")

    service = ReconciliationService()
    evaluator = BenchmarkEvaluator()

    try:
        print(f"1. Loading inference records & running deterministic reconciliation...")
        batch_result = service.reconcile_from_disk(dataset_id)
        metrics = batch_result.performance_metrics
        print(f"   Reconciled {batch_result.total_cases} cases in {metrics.total_wall_clock_time_ms:.2f}ms ({metrics.throughput_records_per_sec:.1f} rec/s)")
        print(f"   Latency: P50={metrics.latency_p50_ms:.3f}ms, P95={metrics.latency_p95_ms:.3f}ms, P99={metrics.latency_p99_ms:.3f}ms")

        print(f"2. Loading isolated ground truth & computing evaluation metrics...")
        report = evaluator.evaluate_from_disk(
            dataset_id=dataset_id,
            results=batch_result.results,
            performance_metrics=metrics,
        )

        print("\n" + "=" * 60)
        print(f"BENCHMARK RESULTS: {dataset_id}")
        print("=" * 60)
        print(f"Overall Accuracy         : {report.overall_accuracy * 100:.2f}% ({report.correct_classifications}/{report.total_records})")
        print(f"Macro-Averaged F1        : {report.macro_f1:.4f}")
        print(f"False-Match Rate (FMR)   : {report.false_match_rate * 100:.2f}% (Target: 0.0%)")
        print(f"False-Unresolved Rate    : {report.false_unresolved_rate * 100:.2f}%")
        print("-" * 60)
        print(f"{'Class':<22} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'Support':<8}")
        print("-" * 60)
        for c_name, c_met in report.per_class_metrics.items():
            print(f"{c_name:<22} | {c_met.precision * 100:>8.2f}% | {c_met.recall * 100:>8.2f}% | {c_met.f1_score:>10.4f} | {c_met.support:>8}")
        print("=" * 60)

        if report.failures:
            print(f"\nMisclassifications ({len(report.failures)}):")
            for f in report.failures[:5]:
                print(f"  - Case {f.case_id} (Order {f.order_id}): Actual={f.actual_class}, Predicted={f.predicted_class} [{f.reason_code}]")
            if len(report.failures) > 5:
                print(f"  ... and {len(report.failures) - 5} more.")

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2)
            print(f"\nSaved benchmark evaluation report to: {out.resolve()}")

        return 0
    except Exception as e:
        print(f"ERROR: Benchmark execution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="METFI Benchmark Runner")
    parser.add_argument("--dataset-id", default="dev_500", help="Dataset identifier to benchmark (e.g. dev_500, stress_5000)")
    parser.add_argument("--output", default=None, help="Path to write JSON evaluation report")

    args = parser.parse_args()
    code = run_benchmark(args.dataset_id, args.output)
    sys.exit(code)


if __name__ == "__main__":
    main()
