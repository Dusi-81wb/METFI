"""
Pydantic schemas for AI Investigation API requests, structured LLM envelopes, and responses.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifierStatus,
)
from app.domain.reconciliation_result import ReconciliationResult


class EvidenceReferenceSchema(BaseModel):
    """Schema for individual evidence citations."""

    field_path: str = Field(
        description="Path of cited evidence field, e.g. 'monetary.settlement_amount_delta'"
    )
    observed_value: str = Field(description="Exact observed value in evidence")
    significance: str = Field(description="Why this evidence supports the explanation")


class InvestigationLLMResponseSchema(BaseModel):
    """Structured JSON schema for AI Investigator LLM generation."""

    status: InvestigationStatus = Field(
        default=InvestigationStatus.INVESTIGATED,
        description="Investigation status: INVESTIGATED, INSUFFICIENT_EVIDENCE, etc.",
    )
    root_cause_category: RootCauseCategory = Field(
        default=RootCauseCategory.UNIDENTIFIED_ROOT_CAUSE,
        description="Categorized operational or financial root cause",
    )
    primary_explanation: str = Field(
        description="Concise factual explanation grounded in context evidence"
    )
    evidence_references: list[EvidenceReferenceSchema] = Field(
        default_factory=list, description="Explicit citations to fields in case context"
    )
    alternative_explanations: list[str] = Field(
        default_factory=list, description="Alternative hypotheses considered"
    )
    missing_evidence: list[str] = Field(
        default_factory=list, description="Missing data required for conclusive determination"
    )
    uncertainty_notes: str | None = Field(
        default=None, description="Notes on ambiguities or unknown policies"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Qualitative confidence: HIGH, MEDIUM, LOW"
    )
    confidence_score: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Advisory confidence score between 0.0 and 1.0"
    )
    recommended_action: BoundedRecommendation = Field(
        default=BoundedRecommendation.REVIEW_REQUIRED,
        description="Proposed bounded action: AUTO_RECONCILE, REVIEW_REQUIRED, UNRESOLVED",
    )
    policy_considerations: str | None = Field(
        default=None, description="Relevant contract or tax policies applied"
    )


class VerifierLLMResponseSchema(BaseModel):
    """Structured JSON schema for AI Verifier LLM generation."""

    verifier_status: VerifierStatus = Field(
        default=VerifierStatus.VERIFIED,
        description="Verification outcome: VERIFIED, REJECTED, or INSUFFICIENT_EVIDENCE",
    )
    is_evidence_supported: bool = Field(
        default=True, description="True if claims are supported by context evidence"
    )
    are_references_valid: bool = Field(
        default=True, description="True if cited field paths exist in context"
    )
    is_deterministic_truth_preserved: bool = Field(
        default=True, description="True if deterministic truth is not contradicted"
    )
    is_recommendation_safe: bool = Field(
        default=True, description="True if recommendation obeys financial safety rules"
    )
    verifier_notes: str = Field(description="Summary of verifier analysis")
    rejection_reasons: list[str] = Field(
        default_factory=list, description="List of reasons if rejected"
    )


class InvestigationRunRequest(BaseModel):
    """API request payload for running an AI investigation on a case."""

    case_id: str = Field(description="Unique reconciliation case identifier")
    dataset_id: str | None = Field(
        default=None, description="Optional dataset ID if loading from persistence"
    )
    provider_override: str | None = Field(
        default=None, description="Optional AI provider override (e.g. 'mock', 'gemini', 'openai')"
    )
    model_override: str | None = Field(default=None, description="Optional model override string")


class InvestigationRunResponse(BaseModel):
    """API response envelope for a completed AI investigation."""

    case_id: str
    deterministic_result: ReconciliationResult
    investigation: InvestigationResult
    verification: VerificationResult
    final_canonical_status: ExceptionType
    final_policy_outcome: PolicyOutcome
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
