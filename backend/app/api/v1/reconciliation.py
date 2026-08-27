"""FastAPI route handlers for batch reconciliation and evaluation benchmark operations."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.reconciliation_result import BatchReconciliationResult
from app.evaluation.evaluator import BenchmarkEvaluationReport, BenchmarkEvaluator
from app.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


class RunBatchReconciliationRequest(BaseModel):
    """Request payload to trigger batch reconciliation."""

    dataset_id: str | None = Field(
        default=None, description="Named dataset ID on disk (e.g. dev_500, stress_5000)"
    )
    raw_payments: list[dict[str, Any]] | None = Field(
        default=None, description="Optional raw in-memory payment records"
    )
    raw_settlements: list[dict[str, Any]] | None = Field(
        default=None, description="Optional raw in-memory settlement records"
    )
    raw_ledger: list[dict[str, Any]] | None = Field(
        default=None, description="Optional raw in-memory ledger records"
    )


class RunBenchmarkRequest(BaseModel):
    """Request payload to execute benchmark evaluation against ground truth."""

    dataset_id: str = Field(default="dev_500", description="Dataset identifier to benchmark")


@router.post(
    "/run",
    response_model=BatchReconciliationResult,
    status_code=status.HTTP_200_OK,
    summary="Execute batch financial reconciliation",
)
async def run_batch_reconciliation(
    request: RunBatchReconciliationRequest,
) -> BatchReconciliationResult:
    """
    Execute deterministic reconciliation on a dataset or provided payload.
    """
    service = ReconciliationService()

    try:
        if request.raw_payments is not None:
            return service.reconcile_records(
                raw_payments=request.raw_payments,
                raw_settlements=request.raw_settlements or [],
                raw_ledger=request.raw_ledger or [],
                dataset_id=request.dataset_id or "custom_payload",
            )
        elif request.dataset_id:
            return service.reconcile_from_disk(request.dataset_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either dataset_id or raw_payments must be provided.",
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Reconciliation error: {e}"
        ) from e


@router.post(
    "/benchmark",
    response_model=BenchmarkEvaluationReport,
    status_code=status.HTTP_200_OK,
    summary="Execute benchmark against ground truth",
)
async def run_benchmark(request: RunBenchmarkRequest) -> BenchmarkEvaluationReport:
    """
    Execute end-to-end reconciliation and evaluate against isolated ground truth.
    """
    service = ReconciliationService()
    evaluator = BenchmarkEvaluator()

    try:
        batch_result = service.reconcile_from_disk(request.dataset_id)
        return evaluator.evaluate_from_disk(
            dataset_id=request.dataset_id,
            results=batch_result.results,
            performance_metrics=batch_result.performance_metrics,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Benchmark failed: {e}"
        ) from e
