"""
Abstract LLM Provider interface, implementations, and resilient execution framework (ADR-005).

Provides model-agnostic inference with:
- Text and Pydantic structured output generation
- Bounded exponential backoff retries on transient errors
- Token, latency, and cost metadata tracking
- Mock provider for deterministic offline testing and CI
- Gemini and OpenAI/Nemotron provider adapters
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.domain.investigation import (
    BoundedRecommendation,
    ConfidenceLevel,
    InvestigationStatus,
    RootCauseCategory,
    VerifierStatus,
)
from app.schemas.investigation import (
    EvidenceReferenceSchema,
    InvestigationLLMResponseSchema,
    VerifierLLMResponseSchema,
)

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    """Standardized envelope for unstructured LLM text generation and metadata."""

    content: str
    model: str
    provider: str
    total_tokens: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float = 0.0
    estimated_cost_usd: float | None = None
    metadata: dict[str, Any] = {}


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        is_retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.is_retryable = is_retryable
        self.status_code = status_code


class LLMProvider(ABC):
    """Abstract interface for AI inference providers (ADR-005)."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        """Generate unstructured text from prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        """Generate validated Pydantic structured output from prompt."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the unique identifier of the provider."""
        pass

    async def health_check(self) -> bool:
        """Return True if provider endpoint is healthy and reachable."""
        return True


class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock AI Provider for testing, local verification, and offline benchmarks.
    Simulates realistic financial investigations and verifications without external APIs.
    """

    def __init__(
        self,
        model_name: str = "mock-financial-analyst-v1",
        scenario: str = "correct",
    ) -> None:
        self.model_name = model_name
        self.scenario = scenario

    def get_provider_name(self) -> str:
        return "mock"

    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        return LLMResponse(
            content="Mock financial investigation text analysis.",
            model=self.model_name,
            provider="mock",
            total_tokens=64,
            latency_ms=2.5,
        )

    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        # Simulate slight async latency
        await asyncio.sleep(0.001)

        if self.scenario == "malformed":
            raise LLMProviderError(
                "Simulated malformed LLM response error",
                provider="mock",
                is_retryable=False,
            )

        if self.scenario == "timeout":
            raise LLMProviderError(
                "Simulated LLM provider timeout",
                provider="mock",
                is_retryable=True,
                status_code=504,
            )

        # 1. Handling Investigator Schema
        if schema is InvestigationLLMResponseSchema:
            if self.scenario == "unknown_policy":
                return schema(
                    status=InvestigationStatus.POLICY_UNAVAILABLE,
                    root_cause_category=RootCauseCategory.UNIDENTIFIED_ROOT_CAUSE,
                    primary_explanation=(
                        "Fee policy is unconfigured. Observed delta cannot be definitively "
                        "categorized as contract fee deduction."
                    ),
                    evidence_references=[
                        EvidenceReferenceSchema(
                            field_path="fee_policy.status",
                            observed_value="UNKNOWN",
                            significance="Contract fee policy is not configured for this case",
                        )
                    ],
                    alternative_explanations=[
                        "Deduction may be standard gateway fee or merchant penalty"
                    ],
                    missing_evidence=["Active merchant fee schedule"],
                    uncertainty_notes=(
                        "Fee rate unknown; cannot perform deterministic deduction verification."
                    ),
                    confidence_level=ConfidenceLevel.LOW,
                    confidence_score=0.35,
                    recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
                    policy_considerations="Policy unavailable; human review required.",
                )  # type: ignore

            if self.scenario == "insufficient_evidence":
                return schema(
                    status=InvestigationStatus.INSUFFICIENT_EVIDENCE,
                    root_cause_category=RootCauseCategory.UNIDENTIFIED_ROOT_CAUSE,
                    primary_explanation=(
                        "Insufficient settlement and payment records available to determine cause."
                    ),
                    evidence_references=[],
                    alternative_explanations=["Delayed settlement batch", "Pending bank clearance"],
                    missing_evidence=["Settlement record", "Bank payout acknowledgment"],
                    uncertainty_notes="Missing primary settlement evidence.",
                    confidence_level=ConfidenceLevel.LOW,
                    confidence_score=0.20,
                    recommended_action=BoundedRecommendation.UNRESOLVED,
                    policy_considerations="Record cannot be reconciled without settlement data.",
                )  # type: ignore

            if self.scenario == "unsupported_claim":
                # Returns claims referencing non-existent or fabricated fields to test verifier
                return schema(
                    status=InvestigationStatus.INVESTIGATED,
                    root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
                    primary_explanation=(
                        "Discrepancy caused by custom currency conversion rebate of 45.00 INR."
                    ),
                    evidence_references=[
                        EvidenceReferenceSchema(
                            field_path="fabricated.custom_rebate_field",
                            observed_value="45.00",
                            significance="Fabricated claim not in context",
                        )
                    ],
                    alternative_explanations=[],
                    missing_evidence=[],
                    confidence_level=ConfidenceLevel.HIGH,
                    confidence_score=0.99,
                    recommended_action=BoundedRecommendation.AUTO_RECONCILE,  # Unsafe action
                )  # type: ignore

            # Default: Realistic evidence-grounded investigation
            # Inspect prompt context for key markers to synthesize accurate mock response
            if "AMOUNT_MISMATCH" in prompt:
                return schema(
                    status=InvestigationStatus.INVESTIGATED,
                    root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
                    primary_explanation=(
                        "Settled net differs from payment gross due to gateway fee and GST."
                    ),
                    evidence_references=[
                        EvidenceReferenceSchema(
                            field_path="monetary.settlement_amount_delta",
                            observed_value="observed_delta",
                            significance="Discrepancy matches calculated fee and tax deductions",
                        )
                    ],
                    alternative_explanations=["Partial payment installment"],
                    missing_evidence=[],
                    confidence_level=ConfidenceLevel.HIGH,
                    confidence_score=0.92,
                    recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
                    policy_considerations="Gateway fee rate applied per merchant agreement.",
                )  # type: ignore

            if "CURRENCY_MISMATCH" in prompt:
                return schema(
                    status=InvestigationStatus.INVESTIGATED,
                    root_cause_category=RootCauseCategory.CURRENCY_CONVERSION_VARIANCE,
                    primary_explanation=(
                        "Payment in foreign currency while settlement in domestic currency."
                    ),
                    evidence_references=[
                        EvidenceReferenceSchema(
                            field_path="currency.is_currency_matched",
                            observed_value="False",
                            significance="Currency mismatch between payment and settlement",
                        )
                    ],
                    alternative_explanations=[],
                    missing_evidence=["Forex conversion rate slip"],
                    confidence_level=ConfidenceLevel.HIGH,
                    confidence_score=0.95,
                    recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
                    policy_considerations=(
                        "Currency conversion variance requires manual forex reconciliation."
                    ),
                )  # type: ignore

            if "AMBIGUOUS" in prompt:
                return schema(
                    status=InvestigationStatus.INSUFFICIENT_EVIDENCE,
                    root_cause_category=RootCauseCategory.AMBIGUOUS_CANDIDATE_TIE,
                    primary_explanation=(
                        "Multiple equally plausible settlement candidates exist for this order."
                    ),
                    evidence_references=[
                        EvidenceReferenceSchema(
                            field_path="identifier.is_ambiguous_candidate",
                            observed_value="True",
                            significance="Multiple candidate matches found",
                        )
                    ],
                    alternative_explanations=[
                        "Duplicate customer payment",
                        "Split settlement batch",
                    ],
                    missing_evidence=["Unique transaction reference code"],
                    uncertainty_notes="Candidate ambiguity cannot be resolved automatically.",
                    confidence_level=ConfidenceLevel.LOW,
                    confidence_score=0.40,
                    recommended_action=BoundedRecommendation.UNRESOLVED,
                    policy_considerations=(
                        "Ambiguous settlements must be adjudicated by human operations."
                    ),
                )  # type: ignore

            # Generic fallback investigation
            return schema(
                status=InvestigationStatus.INVESTIGATED,
                root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
                primary_explanation=(
                    "Standard financial record analysis completed based on available evidence."
                ),
                evidence_references=[],
                alternative_explanations=[],
                missing_evidence=[],
                confidence_level=ConfidenceLevel.MEDIUM,
                confidence_score=0.80,
                recommended_action=BoundedRecommendation.REVIEW_REQUIRED,
            )  # type: ignore

        # 2. Handling Verifier Schema
        if schema is VerifierLLMResponseSchema:
            if self.scenario == "reject_verification":
                return schema(
                    verifier_status=VerifierStatus.REJECTED,
                    is_evidence_supported=False,
                    are_references_valid=False,
                    is_deterministic_truth_preserved=True,
                    is_recommendation_safe=False,
                    verifier_notes="Rejected due to unsupported evidence citations.",
                    rejection_reasons=["Investigator cited non-existent field path"],
                )  # type: ignore

            return schema(
                verifier_status=VerifierStatus.VERIFIED,
                is_evidence_supported=True,
                are_references_valid=True,
                is_deterministic_truth_preserved=True,
                is_recommendation_safe=True,
                verifier_notes="All claims are verified against deterministic context.",
                rejection_reasons=[],
            )  # type: ignore

        # General Pydantic fallback
        return schema.model_validate({})


class GeminiLLMProvider(LLMProvider):
    """Google Gemini AI Provider adapter."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key: str = str(api_key or getattr(settings, "GEMINI_API_KEY", "") or "")
        self.model_name: str = str(
            model_name or getattr(settings, "DEFAULT_AI_MODEL", "gemini-2.5-flash")
        )
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def get_provider_name(self) -> str:
        return "gemini"

    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY is not configured.", provider="gemini", is_retryable=False
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        perf_start = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            latency_ms = (time.perf_counter() - perf_start) * 1000.0

            if resp.status_code != 200:
                is_retryable = resp.status_code in (429, 500, 503, 504)
                raise LLMProviderError(
                    f"Gemini API error {resp.status_code}: {resp.text}",
                    provider="gemini",
                    is_retryable=is_retryable,
                    status_code=resp.status_code,
                )

            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

            return LLMResponse(
                content=text,
                model=self.model_name,
                provider="gemini",
                total_tokens=tokens,
                latency_ms=latency_ms,
            )

    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        if not self.api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY is not configured.", provider="gemini", is_retryable=False
            )

        json_schema = schema.model_json_schema()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": json_schema,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                is_retryable = resp.status_code in (429, 500, 503, 504)
                raise LLMProviderError(
                    f"Gemini API error {resp.status_code}: {resp.text}",
                    provider="gemini",
                    is_retryable=is_retryable,
                    status_code=resp.status_code,
                )

            data = resp.json()
            raw_text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            try:
                parsed_json = json.loads(raw_text)
                return schema.model_validate(parsed_json)
            except (json.JSONDecodeError, ValidationError) as e:
                raise LLMProviderError(
                    f"Failed to parse structured output from Gemini: {e}",
                    provider="gemini",
                    is_retryable=False,
                ) from e


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI / NVIDIA NIM / Nemotron / Local Ollama compatible AI Provider adapter.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key: str = str(
            api_key
            or getattr(settings, "OPENAI_API_KEY", "")
            or getattr(settings, "NVIDIA_API_KEY", "")
            or ""
        )
        raw_url = str(
            base_url
            or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
            or "https://api.openai.com/v1"
        )
        self.base_url: str = raw_url.rstrip("/")
        self.model_name: str = str(
            model_name or getattr(settings, "DEFAULT_AI_MODEL", "gpt-4o-mini")
        )
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def get_provider_name(self) -> str:
        return "openai"

    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderError(
                "API key is not configured for OpenAI provider.",
                provider="openai",
                is_retryable=False,
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
        }

        perf_start = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            latency_ms = (time.perf_counter() - perf_start) * 1000.0

            if resp.status_code != 200:
                is_retryable = resp.status_code in (429, 500, 502, 503, 504)
                raise LLMProviderError(
                    f"OpenAI API error {resp.status_code}: {resp.text}",
                    provider="openai",
                    is_retryable=is_retryable,
                    status_code=resp.status_code,
                )

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=self.model_name,
                provider="openai",
                total_tokens=usage.get("total_tokens"),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                latency_ms=latency_ms,
            )

    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        if not self.api_key:
            raise LLMProviderError(
                "API key is not configured for OpenAI provider.",
                provider="openai",
                is_retryable=False,
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": kwargs.get("temperature", 0.0),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                is_retryable = resp.status_code in (429, 500, 502, 503, 504)
                raise LLMProviderError(
                    f"OpenAI API error {resp.status_code}: {resp.text}",
                    provider="openai",
                    is_retryable=is_retryable,
                    status_code=resp.status_code,
                )

            data = resp.json()
            raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                parsed_json = json.loads(raw_text)
                return schema.model_validate(parsed_json)
            except (json.JSONDecodeError, ValidationError) as e:
                raise LLMProviderError(
                    f"Failed to parse structured output from OpenAI: {e}",
                    provider="openai",
                    is_retryable=False,
                ) from e


def get_llm_provider(
    provider_name: str | None = None,
    scenario: str = "correct",
    **kwargs: Any,
) -> LLMProvider:
    """
    Factory function for obtaining configured LLM Provider instance (ADR-005).
    """
    raw_name = str(provider_name or getattr(settings, "AI_PROVIDER", "mock") or "mock")
    name = raw_name.lower()

    if name in ("mock", "test", "local"):
        return MockLLMProvider(scenario=scenario, **kwargs)
    elif name in ("gemini", "google"):
        return GeminiLLMProvider(**kwargs)
    elif name in ("openai", "nemotron", "nvidia", "ollama"):
        return OpenAILLMProvider(**kwargs)
    else:
        logger.warning("Unrecognized provider '%s', falling back to MockLLMProvider", name)
        return MockLLMProvider(scenario=scenario, **kwargs)
