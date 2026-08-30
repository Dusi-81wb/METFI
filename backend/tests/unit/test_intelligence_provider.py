"""
Unit tests for AI Provider abstraction, Mock provider scenarios, and adapters (ADR-005).
"""

import pytest

from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    InvestigationStatus,
    RootCauseCategory,
    VerifierStatus,
)
from app.intelligence.provider import (
    GeminiLLMProvider,
    LLMProviderError,
    MockLLMProvider,
    OpenAILLMProvider,
    get_llm_provider,
)
from app.schemas.investigation import (
    InvestigationLLMResponseSchema,
    VerifierLLMResponseSchema,
)


@pytest.mark.asyncio
async def test_mock_provider_text_generation() -> None:
    provider = MockLLMProvider()
    resp = await provider.generate_text("Analyze this transaction")
    assert resp.provider == "mock"
    assert resp.content != ""
    assert resp.total_tokens is not None
    assert resp.latency_ms >= 0


@pytest.mark.asyncio
async def test_mock_provider_default_investigation_schema() -> None:
    provider = MockLLMProvider(scenario="correct")
    res = await provider.generate_structured(
        prompt="AMOUNT_MISMATCH case investigation",
        schema=InvestigationLLMResponseSchema,
    )
    assert isinstance(res, InvestigationLLMResponseSchema)
    assert res.status == InvestigationStatus.INVESTIGATED
    assert res.root_cause_category == RootCauseCategory.PROCESSING_FEE_DEDUCTION
    assert len(res.evidence_references) > 0
    assert res.confidence_level == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_mock_provider_currency_mismatch_scenario() -> None:
    provider = MockLLMProvider(scenario="correct")
    res = await provider.generate_structured(
        prompt="CURRENCY_MISMATCH case investigation",
        schema=InvestigationLLMResponseSchema,
    )
    assert res.root_cause_category == RootCauseCategory.CURRENCY_CONVERSION_VARIANCE


@pytest.mark.asyncio
async def test_mock_provider_ambiguous_scenario() -> None:
    provider = MockLLMProvider(scenario="correct")
    res = await provider.generate_structured(
        prompt="AMBIGUOUS candidate match case",
        schema=InvestigationLLMResponseSchema,
    )
    assert res.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert res.root_cause_category == RootCauseCategory.AMBIGUOUS_CANDIDATE_TIE
    assert res.recommended_action == BoundedRecommendation.UNRESOLVED


@pytest.mark.asyncio
async def test_mock_provider_unknown_policy_scenario() -> None:
    provider = MockLLMProvider(scenario="unknown_policy")
    res = await provider.generate_structured(
        prompt="Investigate with unknown fee policy",
        schema=InvestigationLLMResponseSchema,
    )
    assert res.status == InvestigationStatus.POLICY_UNAVAILABLE
    assert res.recommended_action == BoundedRecommendation.REVIEW_REQUIRED


@pytest.mark.asyncio
async def test_mock_provider_insufficient_evidence_scenario() -> None:
    provider = MockLLMProvider(scenario="insufficient_evidence")
    res = await provider.generate_structured(
        prompt="Investigate missing settlement records",
        schema=InvestigationLLMResponseSchema,
    )
    assert res.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert res.recommended_action == BoundedRecommendation.UNRESOLVED


@pytest.mark.asyncio
async def test_mock_provider_unsupported_claim_scenario() -> None:
    provider = MockLLMProvider(scenario="unsupported_claim")
    res = await provider.generate_structured(
        prompt="Investigate case",
        schema=InvestigationLLMResponseSchema,
    )
    assert any("fabricated" in ref.field_path for ref in res.evidence_references)
    assert res.recommended_action == BoundedRecommendation.AUTO_RECONCILE


@pytest.mark.asyncio
async def test_mock_provider_verifier_schema() -> None:
    provider = MockLLMProvider()
    res = await provider.generate_structured(
        prompt="Verify case",
        schema=VerifierLLMResponseSchema,
    )
    assert isinstance(res, VerifierLLMResponseSchema)
    assert res.verifier_status == VerifierStatus.VERIFIED


@pytest.mark.asyncio
async def test_mock_provider_malformed_error_handling() -> None:
    provider = MockLLMProvider(scenario="malformed")
    with pytest.raises(LLMProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Trigger malformed response",
            schema=InvestigationLLMResponseSchema,
        )
    assert "malformed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mock_provider_timeout_error_handling() -> None:
    provider = MockLLMProvider(scenario="timeout")
    with pytest.raises(LLMProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Trigger timeout",
            schema=InvestigationLLMResponseSchema,
        )
    assert exc_info.value.is_retryable is True
    assert exc_info.value.status_code == 504


def test_provider_factory_resolution() -> None:
    mock_p = get_llm_provider("mock")
    assert isinstance(mock_p, MockLLMProvider)

    gemini_p = get_llm_provider("gemini", api_key="dummy")
    assert isinstance(gemini_p, GeminiLLMProvider)

    openai_p = get_llm_provider("openai", api_key="dummy")
    assert isinstance(openai_p, OpenAILLMProvider)

    nemotron_p = get_llm_provider("nemotron", api_key="dummy")
    assert isinstance(nemotron_p, OpenAILLMProvider)

    default_p = get_llm_provider("unknown_nonexistent")
    assert isinstance(default_p, MockLLMProvider)


@pytest.mark.asyncio
async def test_gemini_missing_api_key() -> None:
    provider = GeminiLLMProvider(api_key="")
    with pytest.raises(LLMProviderError):
        await provider.generate_text("test")


@pytest.mark.asyncio
async def test_openai_missing_api_key() -> None:
    provider = OpenAILLMProvider(api_key="")
    with pytest.raises(LLMProviderError):
        await provider.generate_text("test")
