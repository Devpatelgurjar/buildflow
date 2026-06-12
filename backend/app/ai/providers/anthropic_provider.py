# app/ai/providers/anthropic_provider.py
import json
from typing import Any

from pydantic import BaseModel

from app.ai.base import AIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderException, AIResponseValidationException
from app.schemas.chat import ContextMessage


class AnthropicProvider(AIProvider):
    """
    Anthropic provider using the anthropic Python SDK.
    Supports Claude 3.5 Sonnet and any Messages API-compatible model.

    Key difference from OpenAI: system prompt is a top-level parameter,
    not a message role — handled transparently here.
    """

    provider_name = "anthropic"

    def __init__(self):
        try:
            import anthropic as anthropic_sdk
            self._sdk = anthropic_sdk
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in environment")

        self._client = self._sdk.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.ai_model or "claude-sonnet-4-20250514"
        self._max_tokens = settings.ai_max_tokens

    async def complete(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            api_messages = [{"role": m.role, "content": m.content} for m in messages
                           if m.role != "system"]  # Anthropic system goes top-level

            response = await self._client.messages.create(
                model=kwargs.get("model", self._model),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                system=system_prompt or "",
                messages=api_messages,
            )
            return response.content[0].text
        except Exception as e:
            raise AIProviderException(provider=self.provider_name, detail=str(e))

    async def complete_structured(
        self,
        messages: list[ContextMessage],
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> BaseModel:
        json_instruction = (
            f"\n\nRespond ONLY with a valid JSON object matching this schema:\n"
            f"{json.dumps(response_schema.model_json_schema(), indent=2)}\n"
            f"No markdown, no explanation — pure JSON only."
        )
        augmented_system = (system_prompt or "") + json_instruction

        raw = await self.complete(
            messages=messages,
            system_prompt=augmented_system,
            **kwargs,
        )

        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(cleaned)
            return response_schema.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise AIResponseValidationException(
                f"Could not parse {response_schema.__name__} from model output: {e}\nRaw: {raw[:300]}"
            )