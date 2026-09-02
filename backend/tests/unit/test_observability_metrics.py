"""
Unit tests for OperationalMetricsTracker and structured telemetry recording.
"""

import pytest

from app.core.observability import OperationalMetricsTracker


@pytest.mark.asyncio
async def test_observability_metrics_tracker_lifecycle() -> None:
    tracker = OperationalMetricsTracker()
    await tracker.reset()

    # Record latencies
    await tracker.record_latency("reconciliation", 10.0)
    await tracker.record_latency("reconciliation", 20.0)
    await tracker.record_latency("reconciliation", 30.0)

    # Increment counters
    await tracker.increment_counter("cases_reconciled_total", 3)
    await tracker.increment_counter("ai_inferences_total", 1)

    # Record error
    await tracker.record_error("UNAUTHORIZED_ACTION")

    summary = await tracker.get_summary()

    assert summary["counters"]["cases_reconciled_total"] == 3
    assert summary["counters"]["ai_inferences_total"] == 1
    assert summary["errors"]["UNAUTHORIZED_ACTION"] == 1

    rec_lat = summary["latencies"]["reconciliation"]
    assert rec_lat["count"] == 3
    assert rec_lat["avg_ms"] == 20.0
    assert rec_lat["min_ms"] == 10.0
    assert rec_lat["max_ms"] == 30.0
