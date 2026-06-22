# backend/app/agents/openrouter_client.py
"""Unified model client.

Routes requests to either:
  - Google Generative AI SDK  (model names starting with "gemini")
  - OpenRouter via OpenAI SDK (everything else)

Both expose the same generate_content_async / .text interface so agent
files need no changes when the default model changes.
"""

import structlog
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import get_settings

logger = structlog.get_logger()

# --- OpenRouter client (lazy singleton) ---
_openrouter_client: Optional[AsyncOpenAI] = None


def _get_openrouter_client() -> AsyncOpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        settings = get_settings()
        _openrouter_client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(120.0)),
        )
    return _openrouter_client


# --- Gemini client (lazy configure) ---
_gemini_configured = False


def _ensure_gemini():
    global _gemini_configured
    if not _gemini_configured:
        import google.generativeai as genai
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_configured = True


class OpenRouterResponse:
    """Minimal response wrapper; mirrors Gemini's response.text API."""
    def __init__(self, text: str):
        self.text = text


class OpenRouterModel:
    """Unified model wrapper.

    Pass any model name:
      - "gemini-2.0-flash", "gemini-1.5-flash", etc. → Google AI SDK (free tier)
      - "meta-llama/...", "google/gemma-...", etc.    → OpenRouter
    """

    def __init__(self, *, model_name: str, system_instruction: str):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self._use_gemini = model_name.startswith("gemini")

    async def generate_content_async(
        self, user_prompt: str, *, generation_config: Optional[object] = None
    ) -> OpenRouterResponse:
        if self._use_gemini:
            return await self._gemini_call(user_prompt, generation_config)
        return await self._openrouter_call(user_prompt, generation_config)

    # ------------------------------------------------------------------
    async def _gemini_call(self, user_prompt: str, generation_config) -> OpenRouterResponse:
        import google.generativeai as genai
        from google.generativeai.types import GenerationConfig

        _ensure_gemini()

        gc = None
        if generation_config is not None:
            gc = GenerationConfig(
                max_output_tokens=getattr(generation_config, "max_output_tokens", None),
                response_mime_type=getattr(generation_config, "response_mime_type", None),
            )

        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=self.system_instruction,
        )
        try:
            response = await model.generate_content_async(user_prompt, generation_config=gc)
            return OpenRouterResponse(text=response.text)
        except Exception as exc:
            logger.error("gemini_error", model=self.model_name, error=str(exc))
            raise

    # ------------------------------------------------------------------
    async def _openrouter_call(self, user_prompt: str, generation_config) -> OpenRouterResponse:
        max_tokens = getattr(generation_config, "max_output_tokens", None)
        mime_type = getattr(generation_config, "response_mime_type", None)

        kwargs: dict = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": user_prompt},
            ],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if mime_type == "application/json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await _get_openrouter_client().chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return OpenRouterResponse(text=content)
        except Exception as exc:
            import openai
            if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
                logger.error("openrouter_auth_error", model=self.model_name, error=str(exc))
                raise ValueError(f"OpenRouter Authentication Failed: {str(exc)}") from exc
            logger.error("openrouter_error", model=self.model_name, error=str(exc))
            raise
