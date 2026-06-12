# app/ai/providers/openai_provider.py
import json
from typing import Any

from pydantic import BaseModel

from app.ai.base import AIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderException, AIResponseValidationException
from app.schemas.chat import ContextMessage


class OpenAIProvider(AIProvider):
    """
    OpenAI provider using the openai Python SDK.
    Supports GPT-4o and any chat-completion-compatible model.
    """

    provider_name = "openai"

    def __init__(self):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package not installed. Run: pip install openai"
            )
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment")

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.ai_model
        self._max_tokens = settings.ai_max_tokens
        self._temperature = settings.ai_temperature

    def _build_messages(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None,
    ) -> list[dict]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        result.extend([{"role": m.role, "content": m.content} for m in messages])
        return result

    async def complete(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=kwargs.get("model", self._model),
                messages=self._build_messages(messages, system_prompt),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
            return response.choices[0].message.content or ""
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
            temperature=0.2,  # Lower temperature for structured output
            **kwargs,
        )

        # Strip markdown fences if model adds them despite instructions
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(cleaned)
            return response_schema.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise AIResponseValidationException(
                f"Could not parse {response_schema.__name__} from model output: {e}\nRaw: {raw[:300]}"
            )