# backend/app/agents/openrouter_client.py
"""Shared OpenRouter client wrapper.

Provides an interface compatible with the existing generate_content_with_retry utility,
which expects a model object exposing an async ``generate_content_async`` method.
"""

import openai
import structlog
from app.config import get_settings
from typing import Optional

logger = structlog.get_logger()

class OpenRouterResponse:
    """Simple response wrapper mimicking Gemini's response API used in the code base."""

    def __init__(self, text: str):
        self.text = text

class OpenRouterModel:
    """Thin wrapper around OpenAI-compatible API (OpenRouter).

    Parameters
    ----------
    model_name: str
        The model identifier, e.g. ``openrouter/anthropic/claude-3.5-sonnet``.
    system_instruction: str
        System prompt supplied to the model.
    """

    def __init__(self, *, model_name: str, system_instruction: str):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.settings = get_settings()
        # Configure openai client for OpenRouter
        openai.api_key = self.settings.OPENROUTER_API_KEY
        openai.base_url = getattr(self.settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        # Optional: set organization if needed (not required for OpenRouter)

    async def generate_content_async(self, user_prompt: str, *, generation_config: Optional[object] = None) -> OpenRouterResponse:
        """Generate content using OpenRouter.

        The ``generation_config`` argument mirrors the Gemini config used elsewhere.
        Only ``max_output_tokens`` is honoured; other fields are ignored for now.
        """
        max_tokens = None
        if generation_config and hasattr(generation_config, "max_output_tokens"):
            max_tokens = generation_config.max_output_tokens

        messages = [
            {"role": "system", "content": self.system_instruction},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                # OpenRouter recommends ``temperature`` etc.; defaults are fine.
            )
            content = response.choices[0].message.content
            return OpenRouterResponse(text=content)
        except Exception as exc:
            logger.error("openrouter_error", error=str(exc))
            raise
