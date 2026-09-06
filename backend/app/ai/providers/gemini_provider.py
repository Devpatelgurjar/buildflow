# app/ai/providers/gemini_provider.py
import json
from typing import Any

from pydantic import BaseModel

from app.ai.base import AIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderException, AIResponseValidationException
from app.schemas.chat import ContextMessage


class GeminiProvider(AIProvider):
    """
    Google Gemini provider using the modern google-genai SDK.
    Free tier: Sufficient for development.

    Setup:
        pip install google-genai
        Set in .env:
            AI_PROVIDER=gemini
            GEMINI_API_KEY=your_key_from_aistudio.google.com
            AI_MODEL=gemini-2.5-flash
    """

    provider_name = "gemini"

    def __init__(self):
        try:
            # 1. Use the new official client import path
            from google import genai
            from google.genai import types
            self._genai_mod = genai
            self._types = types
        except ImportError:
            raise RuntimeError(
                "google-genai not installed. Run: pip install google-genai"
            )
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")

        # 2. Instantiate the Client (Use the API key explicitly)
        self._client = genai.Client(api_key=settings.gemini_api_key)
        # Update fallback to the current stable model
        self._model_name = settings.ai_model or "gemini-2.5-flash"

    def _build_contents(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None,
    ) -> tuple[str | None, list[Any]]:
        """
        Gemini separates system_instruction from chat contents.
        Returns (system_instruction, contents_list).
        Gemini roles: 'user' and 'model'.
        """
        system = system_prompt or None

        # Extract system-role messages and merge into system instruction
        system_messages = [m for m in messages if m.role == "system"]
        if system_messages:
            extra = "\n".join(m.content for m in system_messages)
            system = f"{system}\n{extra}" if system else extra

        # The new SDK natively accepts Content objects or dicts matching types.Content
        contents = []
        for m in messages:
            if m.role == "system":
                continue
            gemini_role = "model" if m.role == "assistant" else "user"
            contents.append(
                self._types.Content(
                    role=gemini_role,
                    parts=[self._types.Part.from_text(text=m.content)]
                )
            )

        return system, contents

    async def complete(
        self,
        messages: list[ContextMessage],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            system, contents = self._build_contents(messages, system_prompt)

            # 3. Create a unified generation configuration object
            config = self._types.GenerateContentConfig(
                system_instruction=system,
                temperature=kwargs.get("temperature", settings.ai_temperature),
                max_output_tokens=kwargs.get("max_tokens", settings.ai_max_tokens),
            )

            # 4. Use client.aio for native, non-blocking asynchronous calls
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )

            if not response.text:
                raise AIProviderException(
                    provider=self.provider_name, 
                    detail="Model returned an empty response."
                )

            return response.text

        except Exception as e:
            raise AIProviderException(provider=self.provider_name, detail=str(e))

    async def complete_structured(
        self,
        messages: list[ContextMessage],
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> BaseModel:
        try:
            system, contents = self._build_contents(messages, system_prompt)

            # 5. Native JSON Enforcement: Pass the schema directly to the configuration
            config = self._types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                max_output_tokens=kwargs.get("max_tokens", settings.ai_max_tokens),
                response_mime_type="application/json",
                response_schema=response_schema,  # Directly hands off Pydantic definition
            )

            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )

            raw = response.text
            if not raw:
                raise ValueError("Empty response string received from native structured API.")

            # 6. Parse and return safely; Gemini guarantees conformity to schema
            return response_schema.model_validate_json(raw)

        except Exception as e:
            raise AIResponseValidationException(
                f"Could not parse {response_schema.__name__} from Gemini structured output: {e}"
            )
