# app/ai/factory.py
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.ai.base import AIProvider
from app.core.config import settings


@lru_cache
def _get_provider_instance() -> AIProvider:
    provider = settings.ai_provider.lower()

    if provider == "mock":
        from app.ai.providers.mock_Provider import MockAIProvider
        return MockAIProvider()

    if provider == "openai":
        from app.ai.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if provider == "anthropic":
        from app.ai.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    if provider == "gemini":
        raise NotImplementedError(
            "Gemini provider not yet implemented. "
            "Set AI_PROVIDER=mock for local dev."
        )

    raise ValueError(
        f"Unknown AI provider: '{provider}'. "
        f"Valid options: mock, openai, anthropic"
    )


def get_ai_provider() -> AIProvider:
    return _get_provider_instance()


AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider)]