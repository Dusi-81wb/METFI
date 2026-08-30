"""
AI Verifier Module.

Provides an independent verification layer that checks, tests, and challenges
AI investigation conclusions against deterministic facts, citation validity,
and financial safety boundaries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.core.logging import logger
from app.domain.enums import ExceptionType
from app.domain.investigation import (
    BoundedRecommendation,
    InvestigationResult,
    InvestigationStatus,
    VerificationResult,
    VerifierStatus,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.intelligence.context_builder import CaseContext
from app.intelligence.prompts.verifier_v1 import (
    VERIFIER_SYSTEM_INSTRUCTION,
    VERIFIER_USER_PROMPT_TEMPLATE,
)
from app.intelligence.provider import (
    LLMProvider,
    LLMProviderError,
    get_llm_provider,
)
from app.schemas.investigation import VerifierLLMResponseSchema


class AIVerifier:
    """
    Independent verification controller for AI investigations.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    async def verify_investigation(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        investigation: InvestigationResult,
        case_context: CaseContext,
    ) -> VerificationResult:
        """
        Verify an investigation result against deterministic truth and context evidence.
        """
        rejection_reasons: list[str] = []

        # 1. Deterministic Hard Gate: Citation Validity
        valid_citations = True
        for ref in investigation.evidence_references:
            if (
                "[UNCERTIFIED PATH]" in ref.significance
                or ref.field_path not in case_context.valid_field_paths
            ):
                valid_citations = False
                rejection_reasons.append(
                    f"Invalid evidence citation: field '{ref.field_path}' not present in context."
                )

        # 2. Deterministic Hard Gate: Truth Preservation
        truth_preserved = True
        det_class = deterministic_result.classification

        # Disallow claiming exact match or auto reconcile for currency/missing/duplicate exceptions
        if det_class in (
            ExceptionType.CURRENCY_MISMATCH,
            ExceptionType.MISSING_SETTLEMENT,
            ExceptionType.DUPLICATE_RECORD,
        ):
            if investigation.recommended_action == BoundedRecommendation.AUTO_RECONCILE:
                truth_preserved = False
                rejection_reasons.append(
                    f"Investigation proposed AUTO_RECONCILE for blocking: {det_class.value}"
                )

        # 3. Deterministic Hard Gate: Unknown Fee Policy Safety
        recommendation_safe = True
        if investigation.recommended_action == BoundedRecommendation.AUTO_RECONCILE:
            m = deterministic_result.evidence.monetary
            # If fee policy is unknown and non-zero settlement delta, reject auto-reconcile
            if not case_context.is_fee_policy_known and m.settlement_amount_delta != Decimal(
                "0.00"
            ):
                recommendation_safe = False
                rejection_reasons.append(
                    "AUTO_RECONCILE proposed but contract fee policy is unknown / unconfigured."
                )

            # If fee variance is non-zero under policy, reject auto-reconcile
            if m.fee_variance != Decimal("0.00") or m.tax_variance != Decimal("0.00"):
                recommendation_safe = False
                rejection_reasons.append(
                    f"AUTO_RECONCILE with variance (fee: {m.fee_variance}, tax: {m.tax_variance})."
                )

        # 4. If Investigation was UNAVAILABLE or ERROR
        if investigation.status in (InvestigationStatus.UNAVAILABLE, InvestigationStatus.ERROR):
            return VerificationResult(
                investigation_id=investigation.investigation_id,
                case_id=case_id,
                verifier_status=VerifierStatus.INSUFFICIENT_EVIDENCE,
                is_evidence_supported=False,
                are_references_valid=False,
                is_deterministic_truth_preserved=True,
                is_recommendation_safe=True,
                verifier_notes="Investigation unavailable; defaulted to INSUFFICIENT_EVIDENCE.",
                rejection_reasons=["Investigation result unavailable."],
                verified_at=datetime.now(UTC).isoformat(),
            )

        # 5. LLM Second-Opinion Verification
        llm_verified = True

        user_prompt = VERIFIER_USER_PROMPT_TEMPLATE.format(
            case_context=case_context.rendered_text,
            investigator_output=investigation.model_dump_json(indent=2),
        )

        try:
            verifier_llm_res: VerifierLLMResponseSchema = await self.provider.generate_structured(
                prompt=user_prompt,
                schema=VerifierLLMResponseSchema,
                system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
            )

            if verifier_llm_res.verifier_status == VerifierStatus.REJECTED:
                llm_verified = False
                for r in verifier_llm_res.rejection_reasons:
                    if r not in rejection_reasons:
                        rejection_reasons.append(f"[LLM Verifier] {r}")

        except (LLMProviderError, Exception) as e:
            logger.info(
                "LLM Verifier unavailable (%s), relying on deterministic verification gates.", e
            )

        # 6. Final Synthesis
        is_supported = (
            valid_citations
            and truth_preserved
            and recommendation_safe
            and llm_verified
            and len(rejection_reasons) == 0
        )

        if is_supported:
            final_status = VerifierStatus.VERIFIED
            final_notes = (
                "Verified: Investigation is evidence-grounded, citations are valid, "
                "deterministic truth is preserved, and recommendation is safe."
            )
        else:
            final_status = VerifierStatus.REJECTED
            final_notes = f"Rejected: {'; '.join(rejection_reasons)}"

        return VerificationResult(
            investigation_id=investigation.investigation_id,
            case_id=case_id,
            verifier_status=final_status,
            is_evidence_supported=is_supported,
            are_references_valid=valid_citations,
            is_deterministic_truth_preserved=truth_preserved,
            is_recommendation_safe=recommendation_safe,
            verifier_notes=final_notes,
            rejection_reasons=rejection_reasons,
            verified_at=datetime.now(UTC).isoformat(),
        )
