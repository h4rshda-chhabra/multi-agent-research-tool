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

# --- Gemini OpenAI-compatible clients (lazy singletons per key index) ---
_gemini_clients: dict[int, AsyncOpenAI] = {}


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


def _get_gemini_client(key_index: int = 0) -> AsyncOpenAI:
    if key_index not in _gemini_clients:
        settings = get_settings()
        keys = settings.gemini_keys
        if not keys:
            raise ValueError("No GEMINI_API_KEY configured")
        api_key = keys[key_index % len(keys)]
        _gemini_clients[key_index] = AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(120.0)),
        )
    return _gemini_clients[key_index]


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
        # Gemini's OpenAI-compat endpoint supports response_format; enforce JSON
        # when the caller requests it. Skip for OpenRouter — not all free models
        # support it and it causes 400 errors.
        if self._use_gemini:
            mime = getattr(generation_config, "response_mime_type", None)
            if mime == "application/json":
                kwargs["response_format"] = {"type": "json_object"}

        import openai as _openai
        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return OpenRouterResponse(text=content)
        except _openai.RateLimitError:
            if self._use_gemini:
                logger.warning("gemini_rate_limit_key1", model=self.model_name, fallback="key2")
                client2 = _get_gemini_client(key_index=1)
                response = await client2.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                return OpenRouterResponse(text=content)
            raise
        except Exception as exc:
            if isinstance(exc, (_openai.AuthenticationError, _openai.PermissionDeniedError)):
                provider = "Gemini" if self._use_gemini else "OpenRouter"
                logger.error(f"{provider.lower()}_auth_error", model=self.model_name, error=str(exc))
                raise ValueError(f"{provider} Authentication Failed: {str(exc)}") from exc
            logger.error("model_call_error", model=self.model_name, error=str(exc))
            raise
