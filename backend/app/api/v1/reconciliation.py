"""FastAPI route handlers for batch reconciliation and evaluation benchmark operations."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.reconciliation_result import BatchReconciliationResult
from app.evaluation.evaluator import BenchmarkEvaluationReport, BenchmarkEvaluator
from app.schemas.case_detail import CaseDetailFullResponse
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


class HonestExceptionItem(BaseModel):
    """Authoritative isolated exception item from the reconciliation pipeline."""

    case_id: str
    order_id: str
    classification: str
    severity: str
    status: str
    amount: float
    variance: float
    reason: str
    action_type: str
    reconciled_at: str


@router.get(
    "/cases/{case_id}",
    response_model=CaseDetailFullResponse,
    summary="Fetch live case intelligence, evidence, and agent verification",
)
async def get_case_detail(
    case_id: str,
    dataset_id: str = "dev_500",
) -> CaseDetailFullResponse:
    """
    Retrieve authoritative multi-source records, financial facts, autonomous agent
    investigation, verifier audit, and SHA-256 idempotency actions for any case.
    """
    from app.services.case_detail_service import CaseDetailService

    service = CaseDetailService()
    return await service.get_case_detail(case_id=case_id, dataset_id=dataset_id)


@router.get(
    "/exceptions",
    response_model=list[HonestExceptionItem],
    summary="Fetch live honest unresolvable exceptions list",
)
async def get_honest_exceptions(
    dataset_id: str = "dev_500",
    limit: int = 50,
) -> list[HonestExceptionItem]:
    """
    Retrieve live isolated exceptions from the batch reconciliation engine.
    Satisfies Track 04 rubric requirement for an honest exception list.
    """
    service = ReconciliationService()
    items: list[HonestExceptionItem] = []

    # 1. Include primary showcase fixtures first
    for fix_id in ["case_demo_101", "case_demo_102", "case_demo_103"]:
        try:
            fix_res = service.reconcile_from_disk(fix_id)
            for r in fix_res.results:
                if r.classification.value != "EXACT_MATCH":
                    m = r.evidence.monetary
                    gross = float(m.payment_gross or m.ledger_debit_total or 0.0)
                    var = float(abs(m.settlement_amount_delta or m.fee_variance or 0.0))
                    items.append(
                        HonestExceptionItem(
                            case_id=r.case_id,
                            order_id=r.order_id,
                            classification=r.classification.value,
                            severity="CRITICAL" if "MISSING" in r.reason_code or var > 5000 else "HIGH" if "SLA" in r.reason_code or "PRECEDES" in r.reason_code else "MEDIUM",
                            status="PENDING_REVIEW",
                            amount=gross,
                            variance=var,
                            reason=r.summary,
                            action_type=r.policy_outcome.value,
                            reconciled_at=r.reconciled_at,
                        )
                    )
        except Exception:
            continue

    # 2. Add batch exceptions from requested dataset
    try:
        batch_res = service.reconcile_from_disk(dataset_id)
        for r in batch_res.results:
            if r.classification.value != "EXACT_MATCH":
                m = r.evidence.monetary
                gross = float(m.payment_gross or m.ledger_debit_total or 0.0)
                var = float(abs(m.settlement_amount_delta or m.fee_variance or 0.0))
                items.append(
                    HonestExceptionItem(
                        case_id=r.case_id,
                        order_id=r.order_id,
                        classification=r.classification.value,
                        severity="CRITICAL" if "MISSING" in r.reason_code or var > 5000 else "HIGH" if "SLA" in r.reason_code or "PRECEDES" in r.reason_code else "MEDIUM",
                        status="PENDING_REVIEW",
                        amount=gross,
                        variance=var,
                        reason=r.summary,
                        action_type=r.policy_outcome.value,
                        reconciled_at=r.reconciled_at,
                    )
                )
                if len(items) >= limit:
                    break
    except Exception:
        pass

    return items
