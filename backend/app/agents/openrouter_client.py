# backend/app/agents/openrouter_client.py
"""Shared OpenRouter client wrapper.

Provides an interface compatible with the existing ``generate_content_with_retry``
utility, which expects a model object exposing an async ``generate_content_async``
method returning an object with a ``.text`` attribute (mirroring the old Gemini API).

Uses the openai>=1.0 ``AsyncOpenAI`` client pointed at the OpenRouter endpoint.

NOTE: openai 1.35.0 forwards a ``proxies`` kwarg to httpx, which httpx>=0.28 removed.
We sidestep that by supplying our own ``httpx.AsyncClient`` so openai never builds its
internal wrapper with the unsupported argument.
"""

import structlog
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import get_settings

logger = structlog.get_logger()

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    """Lazily build a single shared AsyncOpenAI client for OpenRouter."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=getattr(
                settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(120.0)),
        )
    return _client


class OpenRouterResponse:
    """Simple response wrapper mimicking Gemini's response API used in the code base."""

    def __init__(self, text: str):
        self.text = text


class OpenRouterModel:
    """Thin wrapper around the OpenAI-compatible OpenRouter chat completions API.

    Parameters
    ----------
    model_name: str
        The model identifier, e.g. ``anthropic/claude-3.5-sonnet``.
    system_instruction: str
        System prompt supplied to the model.
    """

    def __init__(self, *, model_name: str, system_instruction: str):
        self.model_name = model_name
        self.system_instruction = system_instruction

    async def generate_content_async(
        self, user_prompt: str, *, generation_config: Optional[object] = None
    ) -> OpenRouterResponse:
        """Generate content using OpenRouter.

        The ``generation_config`` argument mirrors the Gemini config used elsewhere.
        ``max_output_tokens`` maps to ``max_tokens``; ``response_mime_type ==
        "application/json"`` maps to OpenRouter's JSON ``response_format``.
        """
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
            response = await _get_client().chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return OpenRouterResponse(text=content)
        except Exception as exc:
            import openai
            if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
                logger.error("openrouter_auth_error", model=self.model_name, error=str(exc))
                raise ValueError(f"OpenRouter Authentication Failed: {str(exc)}") from exc
            logger.error("openrouter_error", model=self.model_name, error=str(exc))
            raise
