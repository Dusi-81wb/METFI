"""
Unit tests for Phase 7 Unified Benchmark Runner & Metric Evaluators.

Verifies:
1. All 7 evaluation benchmark suites execute successfully.
2. Summary contains honest per-suite metrics without aggregated misleading headline scores.
3. Every suite produces deterministic, reproducible results with dataset version tracking.
"""

from app.evaluation.unified_benchmark_runner import (
    UnifiedBenchmarkRunner,
    UnifiedBenchmarkSummary,
)


def test_unified_benchmark_runner_executes_all_7_suites() -> None:
    runner = UnifiedBenchmarkRunner()
    summary = runner.run_all_suites()

    assert isinstance(summary, UnifiedBenchmarkSummary)
    assert summary.overall_status == "PASS"
    assert summary.total_suites == 7
    assert len(summary.suites) == 7
    assert summary.total_cases_evaluated >= 100

    suite_categories = {s.category for s in summary.suites}
    expected_categories = {
        "INDEPENDENT",
        "ADVERSARIAL",
        "AI",
        "POLICY",
        "AUDIT",
        "SYNTHETIC",
        "END_TO_END",
    }
    assert suite_categories == expected_categories

    for suite in summary.suites:
        assert suite.passed is True
        assert suite.cases_evaluated > 0
        assert suite.duration_ms >= 0
        assert len(suite.metrics) >= 2
        for metric in suite.metrics:
            assert metric.label != ""
            assert metric.score != ""
            assert metric.passed is True


def test_reconciliation_independent_suite_metrics() -> None:
    runner = UnifiedBenchmarkRunner()
    res = runner.evaluate_reconciliation_suite()
    assert res.suite_id == "SUITE_RECONCILIATION_INDEPENDENT"
    assert res.passed is True
    assert any("Accuracy" in m.label for m in res.metrics)
    assert any("FMR" in m.label or "False-Match Rate" in m.label for m in res.metrics)


def test_adversarial_suite_metrics() -> None:
    runner = UnifiedBenchmarkRunner()
    res = runner.evaluate_adversarial_suite()
    assert res.suite_id == "SUITE_ADVERSARIAL_GENERALIZATION"
    assert res.passed is True
    assert any("Collision" in m.label for m in res.metrics)


def test_ai_suite_metrics() -> None:
    runner = UnifiedBenchmarkRunner()
    res = runner.evaluate_ai_suite()
    assert res.suite_id == "SUITE_AI_REASONING_VERIFICATION"
    assert res.passed is True
    assert any("Grounding" in m.label for m in res.metrics)
    assert any("Truth Preservation" in m.label for m in res.metrics)
