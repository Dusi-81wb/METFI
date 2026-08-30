"""
AI Investigation Service.

Coordinates closed-loop financial exception investigation:
ReconciliationResult ➔ ContextBuilder ➔ AIInvestigator ➔ AIVerifier ➔ VerifiedInvestigationEnvelope

Strict Non-Negotiable:
The deterministic reconciliation result is canonical truth.
AI investigation outputs provide explanation and bounded recommendations,
and cannot override deterministic classifications.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from app.core.logging import logger
from app.domain.canonical import CanonicalTransactionGroup
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.fee_policy import FeeTaxPolicy
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.reconciliation_result import (
    BatchReconciliationResult,
    ReconciliationResult,
)
from app.intelligence.context_builder import AIContextBuilder, CaseContext
from app.intelligence.investigator import AIInvestigator
from app.intelligence.provider import LLMProvider, get_llm_provider
from app.intelligence.verifier import AIVerifier


class InvestigationService:
    """
    Service coordinating evidence-grounded AI investigations and verifications.
    """

    def __init__(
        self,
        investigator: AIInvestigator | None = None,
        verifier: AIVerifier | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or get_llm_provider()
        self.investigator = investigator or AIInvestigator(provider=self.provider)
        self.verifier = verifier or AIVerifier(provider=self.provider)

    async def investigate_case(
        self,
        case_id: str,
        deterministic_result: ReconciliationResult,
        group: CanonicalTransactionGroup | None = None,
        fee_policy: FeeTaxPolicy | None = None,
        force_investigate: bool = False,
    ) -> VerifiedInvestigationEnvelope:
        """
        Investigate a single reconciliation case through the full AI + Verifier loop.
        """
        det_class = deterministic_result.classification
        det_outcome = deterministic_result.policy_outcome

        # 1. Triage: If exact match and not forced, return instant pre-verified envelope
        if det_class == ExceptionType.EXACT_MATCH and not force_investigate:
            inv = InvestigationResult(
                case_id=case_id,
                status=InvestigationStatus.INVESTIGATED,
                root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
                primary_explanation=(
                    "Deterministic exact 3-way match verified. Identifiers and amounts match."
                ),
                evidence_references=[],
                confidence_level=ConfidenceLevel.HIGH,
                confidence_score=1.0,
                recommended_action=BoundedRecommendation.AUTO_RECONCILE,
                policy_considerations="Standard auto-reconciliation eligible.",
                model_metadata={"triage": "exact_match_bypass"},
            )
            ver = VerificationResult(
                investigation_id=inv.investigation_id,
                case_id=case_id,
                verifier_status=VerifierStatus.VERIFIED,
                is_evidence_supported=True,
                are_references_valid=True,
                is_deterministic_truth_preserved=True,
                is_recommendation_safe=True,
                verifier_notes="Exact match verified deterministically.",
                rejection_reasons=[],
            )
            return VerifiedInvestigationEnvelope(
                case_id=case_id,
                deterministic_result=deterministic_result,
                investigation=inv,
                verification=ver,
                final_canonical_status=det_class,
                final_policy_outcome=det_outcome,
                summary=f"Case {case_id}: {det_class.value} - Exact match verified.",
            )

        # 2. Build Context
        case_context: CaseContext = AIContextBuilder.build_case_context(
            case_id=case_id,
            deterministic_result=deterministic_result,
            group=group,
            fee_policy=fee_policy,
        )

        # 3. Run AI Investigator
        inv_result: InvestigationResult = await self.investigator.investigate_case(
            case_id=case_id,
            deterministic_result=deterministic_result,
            group=group,
            fee_policy=fee_policy,
        )

        # 4. Run AI Verifier
        ver_result: VerificationResult = await self.verifier.verify_investigation(
            case_id=case_id,
            deterministic_result=deterministic_result,
            investigation=inv_result,
            case_context=case_context,
        )

        # 5. Synthesize Final Outcomes (Enforcing Deterministic Primacy)
        final_status = det_class  # CANONICAL RULE: Deterministic classification ALWAYS wins

        # Determine Final Policy Outcome
        if ver_result.verifier_status == VerifierStatus.REJECTED:
            # If verifier rejected the AI investigation, force REVIEW_REQUIRED
            final_outcome = PolicyOutcome.REVIEW_REQUIRED
            summary = (
                f"Case {case_id}: {det_class.value} (Investigation Rejected by Verifier: "
                f"{'; '.join(ver_result.rejection_reasons)})"
            )
        elif (
            ver_result.verifier_status == VerifierStatus.VERIFIED
            and inv_result.recommended_action == BoundedRecommendation.AUTO_RECONCILE
            and det_outcome == PolicyOutcome.AUTO_RECONCILE
        ):
            final_outcome = PolicyOutcome.AUTO_RECONCILE
            summary = (
                f"Case {case_id}: {det_class.value} - AI Investigation & Verification verified."
            )
        else:
            final_outcome = (
                det_outcome
                if det_outcome != PolicyOutcome.AUTO_RECONCILE
                else PolicyOutcome.REVIEW_REQUIRED
            )
            summary = f"Case {case_id}: {det_class.value} - {inv_result.primary_explanation}"

        logger.info(
            "Investigation complete for case %s: classification=%s, policy=%s, verifier=%s",
            case_id,
            final_status.value,
            final_outcome.value,
            ver_result.verifier_status.value,
        )

        return VerifiedInvestigationEnvelope(
            case_id=case_id,
            deterministic_result=deterministic_result,
            investigation=inv_result,
            verification=ver_result,
            final_canonical_status=final_status,
            final_policy_outcome=final_outcome,
            summary=summary,
        )

    async def investigate_batch(
        self,
        batch_result: BatchReconciliationResult,
        groups: Sequence[CanonicalTransactionGroup] | None = None,
        fee_policy: FeeTaxPolicy | None = None,
        concurrency_limit: int = 10,
    ) -> list[VerifiedInvestigationEnvelope]:
        """
        Investigate a batch of reconciliation cases with bounded concurrency.
        """
        group_map = {g.case_id: g for g in (groups or [])}
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def _bounded_investigate(res: ReconciliationResult) -> VerifiedInvestigationEnvelope:
            async with semaphore:
                grp = group_map.get(res.case_id)
                return await self.investigate_case(
                    case_id=res.case_id,
                    deterministic_result=res,
                    group=grp,
                    fee_policy=fee_policy,
                )

        tasks = [_bounded_investigate(r) for r in batch_result.results]
        return await asyncio.gather(*tasks)
