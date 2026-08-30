"""
Domain models for AI-assisted exception investigation, evidence grounding, and verification.

Strict Non-Negotiable Rules:
1. Deterministic reconciliation truth is immutable and authoritative.
2. AI investigation results provide explanation, root-cause analysis, and bounded recommendations.
3. Ground truth datasets and generator internals are strictly isolated and inaccessible.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.reconciliation_result import ReconciliationResult


class InvestigationStatus(StrEnum):
    """Execution status of the AI investigation process."""

    INVESTIGATED = "INVESTIGATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    POLICY_UNAVAILABLE = "POLICY_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RootCauseCategory(StrEnum):
    """Categorization of the financial or operational root cause."""

    PROCESSING_FEE_DEDUCTION = "PROCESSING_FEE_DEDUCTION"
    TAX_CALCULATION_DISCREPANCY = "TAX_CALCULATION_DISCREPANCY"
    PARTIAL_SETTLEMENT_INSTALLMENT = "PARTIAL_SETTLEMENT_INSTALLMENT"
    ROUNDING_VARIANCE = "ROUNDING_VARIANCE"
    TIMING_SETTLEMENT_DELAY = "TIMING_SETTLEMENT_DELAY"
    CURRENCY_CONVERSION_VARIANCE = "CURRENCY_CONVERSION_VARIANCE"
    METADATA_TYPO_OR_TRANSLATION = "METADATA_TYPO_OR_TRANSLATION"
    DUPLICATE_SUBMISSION = "DUPLICATE_SUBMISSION"
    MISSING_SETTLEMENT_BATCH = "MISSING_SETTLEMENT_BATCH"
    AMBIGUOUS_CANDIDATE_TIE = "AMBIGUOUS_CANDIDATE_TIE"
    CROSS_CUSTOMER_CONFLICT = "CROSS_CUSTOMER_CONFLICT"
    UNIDENTIFIED_ROOT_CAUSE = "UNIDENTIFIED_ROOT_CAUSE"


class BoundedRecommendation(StrEnum):
    """Bounded, safe operational actions recommended by the AI."""

    AUTO_RECONCILE = "AUTO_RECONCILE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNRESOLVED = "UNRESOLVED"


class ConfidenceLevel(StrEnum):
    """Discrete, unexaggerated qualitative confidence level."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VerifierStatus(StrEnum):
    """Independent verification decision regarding the AI investigation."""

    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceReference(BaseModel):
    """Factual pointer linking an AI claim to an explicit observed field path."""

    model_config = ConfigDict(frozen=True)

    field_path: str = Field(
        description="Dot-notated path of observed evidence (e.g. 'monetary.amount_delta')"
    )
    observed_value: str = Field(
        description="Exact string representation of observed evidence value"
    )
    significance: str = Field(description="Factual reason why this evidence was referenced")


class InvestigationResult(BaseModel):
    """Structured, evidence-grounded AI investigation result."""

    model_config = ConfigDict(frozen=True)

    investigation_id: str = Field(
        default_factory=lambda: f"inv_{uuid4().hex[:12]}",
        description="Unique investigation event identifier",
    )
    case_id: str = Field(description="Associated reconciliation case identifier")
    status: InvestigationStatus = Field(description="Investigation outcome status")
    root_cause_category: RootCauseCategory = Field(
        description="Categorized operational or financial root cause"
    )
    primary_explanation: str = Field(
        description="Concise, factual explanation grounded strictly in provided evidence"
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list, description="Explicit field-level evidence citations"
    )
    alternative_explanations: list[str] = Field(
        default_factory=list, description="Plausible alternative hypotheses considered"
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Information missing from context needed for definitive resolution",
    )
    uncertainty_notes: str | None = Field(
        default=None, description="Explicit notes regarding ambiguity or lack of contract policy"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Qualitative confidence rating (advisory only, never overrides policy)",
    )
    confidence_score: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Advisory model score between 0.0 and 1.0",
    )
    recommended_action: BoundedRecommendation = Field(
        default=BoundedRecommendation.REVIEW_REQUIRED,
        description="Bounded operational action proposed for Policy Engine review",
    )
    policy_considerations: str | None = Field(
        default=None, description="Relevant domain or policy rules noted during investigation"
    )
    model_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Model execution metadata (provider, model, latency, tokens)",
    )
    investigated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of investigation execution",
    )


class VerificationResult(BaseModel):
    """Independent verification decision challenging and checking the AI investigation."""

    model_config = ConfigDict(frozen=True)

    verification_id: str = Field(
        default_factory=lambda: f"ver_{uuid4().hex[:12]}",
        description="Unique verification event identifier",
    )
    investigation_id: str = Field(description="Associated investigation ID")
    case_id: str = Field(description="Associated reconciliation case ID")
    verifier_status: VerifierStatus = Field(description="Final verification decision")
    is_evidence_supported: bool = Field(
        description="True if all claims are backed by verifiable context evidence"
    )
    are_references_valid: bool = Field(
        description="True if all cited field paths exist in the supplied context"
    )
    is_deterministic_truth_preserved: bool = Field(
        description="True if AI does not attempt to contradict authoritative truth"
    )
    is_recommendation_safe: bool = Field(
        description="True if recommended action adheres to strict financial safety constraints"
    )
    verifier_notes: str = Field(
        description="Concise rationale for verification pass, rejection, or insufficiency"
    )
    rejection_reasons: list[str] = Field(
        default_factory=list, description="Specific safety violations or unsupported claims found"
    )
    verified_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 timestamp of verification execution",
    )


class VerifiedInvestigationEnvelope(BaseModel):
    """Immutable envelope binding deterministic truth, AI investigation, and verifier decision."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(description="Reconciliation case identifier")
    deterministic_result: ReconciliationResult = Field(
        description="Authoritative deterministic reconciliation result"
    )
    investigation: InvestigationResult = Field(description="Structured AI investigation result")
    verification: VerificationResult = Field(description="Independent verification decision")
    final_canonical_status: ExceptionType = Field(
        description="Final canonical classification (strictly preserves deterministic truth)"
    )
    final_policy_outcome: PolicyOutcome = Field(
        description="Final policy outcome enforced by verifier and deterministic rules"
    )
    summary: str = Field(description="Executive human-readable summary of the full case outcome")
