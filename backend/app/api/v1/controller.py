"""
FastAPI endpoints for Track 04: AI Finance Controller.
Provides:
- Real-time Books and Cash Position summary
- Execution of the 50+ record synthetic batch finance-ops loop
- Settlement and Cash Position Q&A controller assistant
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.finance_controller import (
    FinanceOpsLoopReport,
    RunFinanceOpsLoopRequest,
    SettlementQAQuery,
    SettlementQAResponse,
)
from app.services.finance_controller_service import FinanceControllerService

controller_router = APIRouter(prefix="/controller", tags=["Finance Controller"])


@controller_router.get(
    "/summary",
    response_model=FinanceOpsLoopReport,
    summary="Get current Books, Cash Position, and Batch loop summary",
)
async def get_controller_summary(
    dataset_id: str = Query("dev_500", description="Dataset identifier"),
) -> FinanceOpsLoopReport:
    """
    Return comprehensive books status (debits/credits invariant),
    reconciled cash position, match rate, and honest exception list.
    """
    service = FinanceControllerService()
    try:
        return service.run_finance_ops_loop(dataset_id=dataset_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate finance controller report for {dataset_id}: {e}",
        ) from e


@controller_router.post(
    "/run-loop",
    response_model=FinanceOpsLoopReport,
    summary="Execute the 50+ record synthetic batch finance-ops loop",
)
async def run_finance_ops_loop(
    request: RunFinanceOpsLoopRequest,
) -> FinanceOpsLoopReport:
    """
    Execute one finance-ops loop across a 50+ record batch of synthetic data.
    Reports throughput, measured accuracy, and the honest exception list.
    """
    service = FinanceControllerService()
    try:
        return service.run_finance_ops_loop(
            dataset_id=request.dataset_id,
            max_records=request.max_records,
            custom_payments=request.payments,
            custom_settlements=request.settlements,
            custom_ledger=request.ledger_entries,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Finance ops loop execution error: {e}",
        ) from e


@controller_router.post(
    "/qa",
    response_model=SettlementQAResponse,
    summary="Settlement and Cash Position Q&A Agent",
)
async def settlement_qa_query(
    request: SettlementQAQuery,
) -> SettlementQAResponse:
    """
    Answer natural language inquiries from the finance controller
    regarding books balance, cash position, unresolvable exceptions, or match rates.
    """
    service = FinanceControllerService()
    try:
        return service.answer_controller_query(
            question=request.question, dataset_id=request.dataset_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Settlement Q&A query processing failed: {e}",
        ) from e
