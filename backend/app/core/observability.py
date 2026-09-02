"""
Operational Observability and Structured Telemetry for METFI.

Tracks stage-level latencies, error categories, AI model inferences,
verifier rejection rates, and safe fallback occurrences.
"""

from __future__ import annotations

import asyncio
from typing import Any


class OperationalMetricsTracker:
    """
    Thread-safe operational telemetry recorder.
    """

    def __init__(self) -> None:
        self._latencies: dict[str, list[float]] = {
            "reconciliation": [],
            "ai_investigation": [],
            "policy_evaluation": [],
            "action_execution": [],
            "audit_write": [],
            "audit_verification": [],
        }
        self._counters: dict[str, int] = {
            "cases_reconciled_total": 0,
            "ai_inferences_total": 0,
            "ai_verification_passes_total": 0,
            "ai_verification_rejections_total": 0,
            "policy_evaluations_total": 0,
            "actions_authorized_total": 0,
            "actions_rejected_total": 0,
            "actions_executed_total": 0,
            "safe_fallbacks_total": 0,
            "reviews_enqueued_total": 0,
            "reviews_escalated_total": 0,
            "audit_integrity_failures_total": 0,
        }
        self._error_counts: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def record_latency(self, stage: str, duration_ms: float) -> None:
        """Record latency observation for a specific processing stage."""
        async with self._lock:
            if stage not in self._latencies:
                self._latencies[stage] = []
            self._latencies[stage].append(duration_ms)

    async def increment_counter(self, name: str, count: int = 1) -> None:
        """Increment a structured operational counter."""
        async with self._lock:
            self._counters[name] = self._counters.get(name, 0) + count

    async def record_error(self, category: str) -> None:
        """Record occurrence of a categorized error."""
        async with self._lock:
            self._error_counts[category] = self._error_counts.get(category, 0) + 1

    async def get_summary(self) -> dict[str, Any]:
        """Produce an aggregated operational telemetry summary."""
        async with self._lock:
            latency_summary: dict[str, dict[str, float]] = {}
            for stage, vals in self._latencies.items():
                if vals:
                    avg_val = sum(vals) / len(vals)
                    p95_index = int(len(vals) * 0.95)
                    sorted_vals = sorted(vals)
                    p95_val = sorted_vals[min(p95_index, len(vals) - 1)]
                    latency_summary[stage] = {
                        "count": len(vals),
                        "avg_ms": round(avg_val, 2),
                        "p95_ms": round(p95_val, 2),
                        "min_ms": round(min(vals), 2),
                        "max_ms": round(max(vals), 2),
                    }
                else:
                    latency_summary[stage] = {"count": 0, "avg_ms": 0.0, "p95_ms": 0.0}

            return {
                "counters": dict(self._counters),
                "errors": dict(self._error_counts),
                "latencies": latency_summary,
            }

    async def reset(self) -> None:
        """Reset all metric buffers (primarily for isolated test fixtures)."""
        async with self._lock:
            for k in self._latencies:
                self._latencies[k] = []
            for k in self._counters:
                self._counters[k] = 0
            self._error_counts.clear()


# Global singleton instance for application runtime metrics
metrics_tracker = OperationalMetricsTracker()
