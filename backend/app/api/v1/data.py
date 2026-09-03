"""FastAPI route handlers for sample dataset inspection and on-demand random data generation."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.domain.reconciliation_result import BatchReconciliationResult
from app.schemas.data import (
    DatasetMetadata,
    RandomGenerationRequest,
    RandomGenerationResponse,
    SampleDataResponse,
)
from app.services.reconciliation_service import ReconciliationService
from app.services.sample_data_service import SampleDataService

data_router = APIRouter(prefix="/data", tags=["Sample Data & Randomizer"])


@data_router.get(
    "/datasets",
    response_model=list[DatasetMetadata],
    summary="List available sample and demo datasets",
)
async def list_available_datasets() -> list[DatasetMetadata]:
    """Return catalog of available demo datasets with record counts and descriptions."""
    service = SampleDataService()
    return service.get_available_datasets()


@data_router.get(
    "/sample",
    response_model=SampleDataResponse,
    summary="Fetch paginated sample records from operational feeds",
)
async def get_sample_records(
    dataset_id: str = Query(
        "dev_500", description="Dataset identifier (e.g. dev_500, case_demo_101)"
    ),
    source: str = Query(
        "all", description="Source feed: 'all', 'payments', 'settlements', 'ledger'"
    ),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(25, ge=1, le=100, description="Limit of records per page"),
    search: str | None = Query(None, description="Optional text filter across IDs and accounts"),
) -> SampleDataResponse:
    """Fetch paginated multi-source records for display and verification."""
    service = SampleDataService()
    try:
        return service.get_sample_data(
            dataset_id=dataset_id,
            source=source,
            offset=offset,
            limit=limit,
            search=search,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load sample data for {dataset_id}: {e}",
        ) from e


@data_router.post(
    "/generate-random",
    response_model=RandomGenerationResponse,
    summary="Generate randomized records with entropy controls",
)
async def generate_random_transactions(
    request: RandomGenerationRequest,
) -> RandomGenerationResponse:
    """
    Generate randomized synthetic transaction records across feeds.
    Temperature parameter (0.0 to 1.0) controls the likelihood of discrepancies.
    """
    service = SampleDataService()
    try:
        return service.generate_random_records(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Random generation error: {e}",
        ) from e


@data_router.post(
    "/test-reconciliation",
    response_model=BatchReconciliationResult,
    summary="Run deterministic reconciliation on generated/in-memory records",
)
async def test_reconcile_generated(
    payload: dict[str, Any],
) -> BatchReconciliationResult:
    """
    Execute deterministic reconciliation on client-provided or randomized records.
    Returns matched candidates, detected discrepancies, and rule execution metrics.
    """
    raw_payments = payload.get("payments", [])
    raw_settlements = payload.get("settlements", [])
    raw_ledger = payload.get("ledger_entries", [])
    dataset_id = payload.get("dataset_id", "interactive_random_batch")

    reconciliation_service = ReconciliationService()
    try:
        return reconciliation_service.reconcile_records(
            raw_payments=raw_payments,
            raw_settlements=raw_settlements,
            raw_ledger=raw_ledger,
            dataset_id=dataset_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Interactive reconciliation failed: {e}",
        ) from e
