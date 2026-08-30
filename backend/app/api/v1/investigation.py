"""
FastAPI route handlers for AI exception investigation and verification operations.
"""

from fastapi import APIRouter, HTTPException, status

from app.domain.investigation import VerifiedInvestigationEnvelope
from app.intelligence.provider import get_llm_provider
from app.schemas.investigation import (
    InvestigationRunRequest,
    InvestigationRunResponse,
)
from app.services.investigation_service import InvestigationService
from app.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/investigation", tags=["AI Investigation"])


@router.post(
    "/run",
    response_model=InvestigationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute evidence-grounded AI investigation and verification on a case",
)
async def run_investigation(request: InvestigationRunRequest) -> InvestigationRunResponse:
    """
    Investigate a specific reconciliation case through the AI + Verifier pipeline.
    """
    rec_service = ReconciliationService()
    dataset_id = request.dataset_id or "dev_500"

    try:
        batch_result = rec_service.reconcile_from_disk(dataset_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found on disk: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dataset: {e}",
        ) from e

    # Locate the target case
    target_case = next((r for r in batch_result.results if r.case_id == request.case_id), None)
    if not target_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case ID '{request.case_id}' not found in dataset '{dataset_id}'.",
        )

    # Initialize Provider & Service
    provider = get_llm_provider(
        provider_name=request.provider_override,
        model_name=request.model_override,
    )
    inv_service = InvestigationService(provider=provider)

    try:
        envelope: VerifiedInvestigationEnvelope = await inv_service.investigate_case(
            case_id=request.case_id,
            deterministic_result=target_case,
            force_investigate=True,
        )

        return InvestigationRunResponse(
            case_id=envelope.case_id,
            deterministic_result=envelope.deterministic_result,
            investigation=envelope.investigation,
            verification=envelope.verification,
            final_canonical_status=envelope.final_canonical_status,
            final_policy_outcome=envelope.final_policy_outcome,
            summary=envelope.summary,
            metadata={
                "provider": provider.get_provider_name(),
                "dataset_id": dataset_id,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation failed: {e}",
        ) from e
