# backend/app/agents/openrouter_client.py
"""Unified model client.

Routes requests to either:
  - Gemini via its OpenAI-compatible endpoint (model names starting with "gemini")
  - OpenRouter via OpenAI SDK (everything else)

Both use the same openai.AsyncOpenAI interface so switching models requires
no changes in agent files.
"""

import structlog
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import get_settings

logger = structlog.get_logger()

# --- OpenRouter client (lazy singleton) ---
_openrouter_client: Optional[AsyncOpenAI] = None

# --- Gemini OpenAI-compatible client (lazy singleton) ---
_gemini_client: Optional[AsyncOpenAI] = None


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


def _get_gemini_client() -> AsyncOpenAI:
    global _gemini_client
    if _gemini_client is None:
        settings = get_settings()
        _gemini_client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(120.0)),
        )
    return _gemini_client


class OpenRouterResponse:
    """Minimal response wrapper; mirrors Gemini's response.text API."""
    def __init__(self, text: str):
        self.text = text


class OpenRouterModel:
    """Unified model wrapper.

    Pass any model name:
      - "gemini-2.5-flash", "gemini-2.0-flash", etc. → Gemini OpenAI-compatible endpoint
      - "meta-llama/...", "google/gemma-...", etc.    → OpenRouter
    """

    def __init__(self, *, model_name: str, system_instruction: str):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self._use_gemini = model_name.startswith("gemini")

    async def generate_content_async(
        self, user_prompt: str, *, generation_config: Optional[object] = None
    ) -> OpenRouterResponse:
        max_tokens = getattr(generation_config, "max_output_tokens", None)

        client = _get_gemini_client() if self._use_gemini else _get_openrouter_client()

        kwargs: dict = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": user_prompt},
            ],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        # response_format / json_object mode is intentionally omitted — not all
        # models support it and it causes 400 errors. Agents enforce JSON output
        # via system prompts + markdown stripping.

        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return OpenRouterResponse(text=content)
        except Exception as exc:
            import openai
            if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
                provider = "Gemini" if self._use_gemini else "OpenRouter"
                logger.error(f"{provider.lower()}_auth_error", model=self.model_name, error=str(exc))
                raise ValueError(f"{provider} Authentication Failed: {str(exc)}") from exc
            logger.error("model_call_error", model=self.model_name, error=str(exc))
            raise
