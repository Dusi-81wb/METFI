"""
FastAPI Router for Phase 7 Evaluation Benchmarks.

Provides endpoints to:
1. GET /api/v1/benchmarks/summary: Get unified evaluation benchmark metrics across all 7 suites.
2. POST /api/v1/benchmarks/run: Trigger on-demand benchmark evaluation suite execution.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.evaluation.unified_benchmark_runner import (
    UnifiedBenchmarkRunner,
    UnifiedBenchmarkSummary,
)

benchmarks_router = APIRouter(prefix="/benchmarks", tags=["Evaluation & Governance Benchmarks"])


@benchmarks_router.get("/summary", response_model=UnifiedBenchmarkSummary)
async def get_benchmark_summary() -> UnifiedBenchmarkSummary:
    """
    Get latest independent, adversarial, AI, policy, and audit evaluation metrics.
    """
    runner = UnifiedBenchmarkRunner()
    return runner.run_all_suites()


@benchmarks_router.post("/run", response_model=UnifiedBenchmarkSummary)
async def run_benchmark_evaluation() -> UnifiedBenchmarkSummary:
    """
    Trigger live execution of all 7 Phase 7 evaluation benchmark suites.
    """
    runner = UnifiedBenchmarkRunner()
    return runner.run_all_suites()
