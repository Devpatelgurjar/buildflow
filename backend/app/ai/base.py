# app/ai/base.py
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.schemas.chat import ContextMessage


class   AIProvider(ABC):
    """
    Abstract interface for all AI/LLM providers.

    Rules:
    - Providers know nothing about DB models or HTTP.
    - They receive plain Python types; return plain Python types.
    - Structured output is validated by the caller via Pydantic, not here.
    - All methods are async — providers are always I/O bound.

    Adding a new provider:
    1. Subclass AIProvider
    2. Implement complete() and complete_structured()
    3. Register in ai/factory.py
    4. Set AI_PROVIDER=yourprovider in .env
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a list of messages and return the assistant's text response.

        Args:
            messages:      Conversation history in [{role, content}] format.
            system_prompt: Optional system-level instruction (injected first).
            **kwargs:      Provider-specific overrides (temperature, max_tokens, etc.)

        Returns:
            Plain text response from the model.
        """
        ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[ContextMessage],
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> BaseModel:
        """
        Like complete(), but instructs the model to respond in JSON
        and validates the output against response_schema via Pydantic.

        Used for: requirements generation, architecture JSON, diagram metadata.

        Raises:
            AIResponseValidationException if the model output fails schema validation.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier for error messages and logging."""
        ...