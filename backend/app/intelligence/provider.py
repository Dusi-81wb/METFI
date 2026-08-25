"""Abstract LLM Provider interface and implementations according to ADR-005."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    """Standardized envelope for LLM text and metadata responses."""

    content: str
    model: str
    provider: str
    total_tokens: int | None = None
    metadata: dict[str, Any] = {}


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


class MockLLMProvider(LLMProvider):
    """Mock AI Provider for deterministic local testing and benchmarking."""

    def __init__(self, model_name: str = "mock-evaluator-v1") -> None:
        self.model_name = model_name

    def get_provider_name(self) -> str:
        return "mock"

    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        return LLMResponse(
            content="Mock investigation analysis completed.",
            model=self.model_name,
            provider="mock",
            total_tokens=42,
        )

    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        # Generate default instance for schema
        return schema.model_validate(schema.model_json_schema().get("default", {}))


class GeminiLLMProvider(LLMProvider):
    """Google Gemini AI Provider integration."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.DEFAULT_AI_MODEL

    def get_provider_name(self) -> str:
        return "gemini"

    async def generate_text(
        self, prompt: str, system_instruction: str | None = None, **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        # Runtime API call will be executed in Phase 3
        return LLMResponse(
            content=f"Gemini response for prompt: {prompt[:30]}...",
            model=self.model_name,
            provider="gemini",
        )

    async def generate_structured(
        self, prompt: str, schema: type[T], system_instruction: str | None = None, **kwargs: Any
    ) -> T:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        raise NotImplementedError("Gemini structured inference will be active in Phase 3.")


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Factory function for obtaining configured LLM Provider instance."""
    name = (provider_name or settings.AI_PROVIDER).lower()
    if name == "mock":
        return MockLLMProvider()
    elif name == "gemini":
        return GeminiLLMProvider()
    else:
        logger.warning("Unrecognized provider '%s', falling back to MockLLMProvider", name)
        return MockLLMProvider()
