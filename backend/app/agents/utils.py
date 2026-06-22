import asyncio
import json
import re
import structlog

logger = structlog.get_logger()


def extract_json(raw: str) -> dict:
    """Parse JSON from a model response, tolerating markdown fences and surrounding text."""
    text = raw.strip()
    # Strip markdown fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text.strip())
    # Try direct parse first (fast path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Use raw_decode to find and parse the first valid JSON object in the text,
    # ignoring any leading prose or trailing content after the closing brace.
    decoder = json.JSONDecoder()
    idx = text.find('{')
    while idx != -1:
        try:
            data, _ = decoder.raw_decode(text, idx)
            return data
        except json.JSONDecodeError:
            idx = text.find('{', idx + 1)
    raise ValueError(f"No JSON object found in model response: {text[:200]}")

def _parse_retry_after(exc) -> float | None:
    """Extract retry_after_seconds from an OpenRouter 429 error body, if present."""
    try:
        body = getattr(exc, "body", None) or {}
        if isinstance(body, dict):
            metadata = body.get("error", {}).get("metadata", {})
            val = metadata.get("retry_after_seconds")
            if val is not None:
                return float(val)
    except Exception:
        pass
    return None

async def generate_content_with_retry(model, *args, max_retries=5, initial_delay=35, **kwargs):
    """
    Retry wrapper for OpenRouter / Gemini model calls.
    Handles 429 rate-limit errors with backoff; respects Retry-After when present.
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return await model.generate_content_async(*args, **kwargs)
        except Exception as exc:
            exc_str = str(exc)
            is_rate_limit = (
                "429" in exc_str
                or "Quota exceeded" in exc_str
                or "ResourceExhausted" in exc_str
                or "rate limit" in exc_str.lower()
                or "rate-limited" in exc_str.lower()
            )

            if is_rate_limit and attempt < max_retries:
                # Honour the provider's Retry-After if available, else use backoff
                retry_after = _parse_retry_after(exc)
                wait = max(retry_after + 2, delay) if retry_after else delay
                logger.warning(
                    "rate_limit_hit",
                    attempt=attempt,
                    max_retries=max_retries,
                    retry_delay_seconds=wait,
                    error_preview=exc_str[:200],
                )
                await asyncio.sleep(wait)
                delay = wait * 2
            else:
                raise exc
