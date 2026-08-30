"""
AI Investigator Module.

Executes evidence-grounded exception investigations, identifies root causes,
validates field-level evidence citations, and produces structured recommendations.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from app.core.logging import logger
from app.domain.canonical import CanonicalTransactionGroup
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    EvidenceReference,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
)
from app.domain.reconciliation_result import ReconciliationResult
from app.intelligence.context_builder import AIContextBuilder, CaseContext
from app.intelligence.prompts import (
    CONTEXT_SCHEMA_VERSION,
    INVESTIGATOR_PROMPT_VERSION,
)
from app.intelligence.prompts.investigator_v1 import (
    INVESTIGATOR_SYSTEM_INSTRUCTION,
    INVESTIGATOR_USER_PROMPT_TEMPLATE,
)
from app.intelligence.provider import (
    LLMProvider,
    LLMProviderError,
    get_llm_provider,
)
from app.schemas.investigation import InvestigationLLMResponseSchema


class AIInvestigator:
    """
    Coordinates evidence-grounded financial exception investigations.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    async def investigate_case(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        group: CanonicalTransactionGroup | None = None,
        fee_policy: FeeTaxPolicy | None = None,
    ) -> InvestigationResult:
        """
        Execute an investigation on a reconciliation case.
        """
        perf_start = time.perf_counter()

        # 1. Build Safe, Minimized Case Context
        case_context: CaseContext = AIContextBuilder.build_case_context(
            case_id=case_id,
            deterministic_result=deterministic_result,
            group=group,
            fee_policy=fee_policy,
        )

        user_prompt = INVESTIGATOR_USER_PROMPT_TEMPLATE.format(
            case_context=case_context.rendered_text
        )

        try:
            # 2. Generate Structured Investigation Output
            llm_response: InvestigationLLMResponseSchema = await self.provider.generate_structured(
                prompt=user_prompt,
                schema=InvestigationLLMResponseSchema,
                system_instruction=INVESTIGATOR_SYSTEM_INSTRUCTION,
            )

            latency_ms = (time.perf_counter() - perf_start) * 1000.0

            # 3. Validate Evidence References against Context Whitelist
            validated_references: list[EvidenceReference] = []
            for ref in llm_response.evidence_references:
                field_path = ref.field_path.strip()
                observed_val = ref.observed_value.strip()

                # If cited field path exists in context, record observed value
                if field_path in case_context.valid_field_paths:
                    context_val = case_context.valid_field_paths[field_path]
                    validated_references.append(
                        EvidenceReference(
                            field_path=field_path,
                            observed_value=context_val,
                            significance=ref.significance,
                        )
                    )
                else:
                    # Note citation path not in context
                    validated_references.append(
                        EvidenceReference(
                            field_path=field_path,
                            observed_value=observed_val,
                            significance=f"[UNCERTIFIED PATH] {ref.significance}",
                        )
                    )

            # 4. Unknown Fee Policy Guard
            status = llm_response.status
            rec_action = llm_response.recommended_action
            uncertainty = llm_response.uncertainty_notes

            if not case_context.is_fee_policy_known:
                if (
                    status == InvestigationStatus.INVESTIGATED
                    and llm_response.root_cause_category
                    in (
                        RootCauseCategory.PROCESSING_FEE_DEDUCTION,
                        RootCauseCategory.TAX_CALCULATION_DISCREPANCY,
                    )
                ):
                    status = InvestigationStatus.POLICY_UNAVAILABLE
                    rec_action = BoundedRecommendation.REVIEW_REQUIRED
                    uncertainty = (
                        "Fee policy is unknown / unconfigured. Deductions cannot be "
                        "verified as compliant without contract policy."
                    )

            metadata: dict[str, Any] = {
                "provider": self.provider.get_provider_name(),
                "latency_ms": round(latency_ms, 2),
                "investigator_prompt_version": INVESTIGATOR_PROMPT_VERSION,
                "context_schema_version": CONTEXT_SCHEMA_VERSION,
            }

            return InvestigationResult(
                case_id=case_id,
                status=status,
                root_cause_category=llm_response.root_cause_category,
                primary_explanation=llm_response.primary_explanation,
                evidence_references=validated_references,
                alternative_explanations=llm_response.alternative_explanations,
                missing_evidence=llm_response.missing_evidence,
                uncertainty_notes=uncertainty,
                confidence_level=llm_response.confidence_level,
                confidence_score=llm_response.confidence_score,
                recommended_action=rec_action,
                policy_considerations=llm_response.policy_considerations,
                model_metadata=metadata,
                investigated_at=datetime.now(UTC).isoformat(),
            )

        except (LLMProviderError, Exception) as e:
            latency_ms = (time.perf_counter() - perf_start) * 1000.0
            logger.warning(
                "AI Investigation failed for case %s: %s. Falling back to safe default.",
                case_id,
                e,
            )

            # Safe Deterministic Fallback on Provider Failure
            return InvestigationResult(
                case_id=case_id,
                status=InvestigationStatus.UNAVAILABLE,
                root_cause_category=RootCauseCategory.UNIDENTIFIED_ROOT_CAUSE,
                primary_explanation=(
                    f"AI Investigation unavailable: {e}. Fallback to deterministic outcome."
                ),
                evidence_references=[],
                alternative_explanations=[],
                missing_evidence=["AI investigation response"],
                uncertainty_notes="Inference service offline or failed.",
                confidence_level=ConfidenceLevel.LOW,
                confidence_score=0.0,
                recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
                policy_considerations="Deterministic truth preserved.",
                model_metadata={
                    "provider": self.provider.get_provider_name(),
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                    "is_fallback": True,
                },
                investigated_at=datetime.now(UTC).isoformat(),
            )
