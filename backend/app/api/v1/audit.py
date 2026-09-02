"""
API Router for Immutable Audit Trail, Hash Chain Verification, and Observability.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.audit.service import AuditService
from app.core.observability import metrics_tracker
from app.domain.audit import AuditEvent
from app.schemas.audit import (
    AuditMetricsResponse,
    CaseAuditTrailResponse,
    CaseIntegrityVerificationResponse,
)

audit_router = APIRouter(prefix="/audit", tags=["Audit & Observability"])

# Shared singleton instance for in-memory / service-backed audit operations
_audit_service_instance = AuditService()


def get_audit_service() -> AuditService:
    """Dependency injection factory for AuditService."""
    return _audit_service_instance


@audit_router.get("/cases/{case_id}", response_model=CaseAuditTrailResponse)
async def get_case_audit_trail_endpoint(
    case_id: str,
    service: AuditService = Depends(get_audit_service),
) -> CaseAuditTrailResponse:
    """
    Retrieve the full chronological, tamper-evident audit trail for a reconciliation case.
    """
    events = await service.get_case_audit_trail(case_id)
    return CaseAuditTrailResponse(
        case_id=case_id,
        event_count=len(events),
        events=events,
    )


@audit_router.get("/cases/{case_id}/verify", response_model=CaseIntegrityVerificationResponse)
async def verify_case_integrity_endpoint(
    case_id: str,
    service: AuditService = Depends(get_audit_service),
) -> CaseIntegrityVerificationResponse:
    """
    Run independent cryptographic and lifecycle integrity verification on a case's audit chain.
    """
    result = await service.verify_case_integrity(case_id)
    return CaseIntegrityVerificationResponse(
        case_id=result.case_id,
        status=result.status,
        events_verified_count=result.events_verified_count,
        is_hash_chain_valid=result.is_hash_chain_valid,
        is_sequence_monotonic=result.is_sequence_monotonic,
        is_lifecycle_coherent=result.is_lifecycle_coherent,
        violations=result.violations,
        verified_at=result.verified_at,
    )


@audit_router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event_endpoint(
    event_id: str,
    service: AuditService = Depends(get_audit_service),
) -> AuditEvent:
    """
    Retrieve an individual immutable audit event by its unique event ID.
    """
    event = await service.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event with ID '{event_id}' not found.",
        )
    return event


@audit_router.get("/metrics", response_model=AuditMetricsResponse)
async def get_audit_metrics_endpoint() -> AuditMetricsResponse:
    """
    Retrieve structured operational telemetry, latency distributions, and error categories.
    """
    summary = await metrics_tracker.get_summary()
    return AuditMetricsResponse(
        counters=summary["counters"],
        errors=summary["errors"],
        latencies=summary["latencies"],
    )
