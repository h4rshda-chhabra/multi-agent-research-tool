import asyncio
import structlog

logger = structlog.get_logger()

async def generate_content_with_retry(model, *args, max_retries=5, initial_delay=6, **kwargs):
    """
    Wrapper around Gemini's generate_content_async that automatically handles
    ResourceExhausted (429) rate limit and quota exceeded errors using
    exponential backoff.
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return await model.generate_content_async(*args, **kwargs)
        except Exception as exc:
            exc_str = str(exc)
            # Detect 429 rate limit or quota exceeded errors
            is_rate_limit = "429" in exc_str or "Quota exceeded" in exc_str or "ResourceExhausted" in exc_str or "rate limit" in exc_str.lower()
            
            if is_rate_limit and attempt < max_retries:
                logger.warning(
                    "gemini_rate_limit_hit",
                    attempt=attempt,
                    max_retries=max_retries,
                    retry_delay_seconds=delay,
                    error_preview=exc_str[:150]
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff (6s, 12s, 24s, 48s)
            else:
                # Re-raise the exception if not a 429, or if we have exhausted all retry attempts
                raise exc
