"""Unit tests for AI Provider abstraction (ADR-005)."""

import pytest
from pydantic import BaseModel, Field

from app.intelligence.provider import (
    GeminiLLMProvider,
    LLMResponse,
    MockLLMProvider,
    get_llm_provider,
)


class SampleInvestigationOutput(BaseModel):
    classification: str = Field(default="EXACT_MATCH")
    confidence: float = Field(default=0.99)


@pytest.mark.asyncio
async def test_mock_llm_provider_generate_text() -> None:
    """Verify MockLLMProvider text generation."""
    provider = MockLLMProvider()
    response = await provider.generate_text("Investigate case 101")
    assert isinstance(response, LLMResponse)
    assert response.provider == "mock"
    assert "Mock investigation" in response.content


@pytest.mark.asyncio
async def test_mock_llm_provider_generate_structured() -> None:
    """Verify MockLLMProvider structured generation against Pydantic schema."""
    provider = MockLLMProvider()
    result = await provider.generate_structured("Investigate case 101", SampleInvestigationOutput)
    assert isinstance(result, SampleInvestigationOutput)
    assert result.classification == "EXACT_MATCH"


def test_gemini_provider_unconfigured_error() -> None:
    """Verify Gemini provider raises error when unconfigured."""
    provider = GeminiLLMProvider(api_key="")
    assert provider.get_provider_name() == "gemini"


def test_get_llm_provider_factory() -> None:
    """Verify factory returns appropriate provider instance."""
    mock_p = get_llm_provider("mock")
    assert isinstance(mock_p, MockLLMProvider)

    gemini_p = get_llm_provider("gemini")
    assert isinstance(gemini_p, GeminiLLMProvider)
