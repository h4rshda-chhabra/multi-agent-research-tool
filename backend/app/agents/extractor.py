import asyncio
import structlog
import httpx
from types import SimpleNamespace
from app.agents.openrouter_client import OpenRouterModel
from bs4 import BeautifulSoup

from app.config import get_settings
from app.agents.state import ResearchState
from app.agents.utils import generate_content_with_retry, extract_json

logger = structlog.get_logger()
settings = get_settings()

EXTRACTOR_SYSTEM = """You are a research extraction specialist. Extract structured information from the provided source content.

Return ONLY valid JSON — no markdown fences, no extra text:
{
  "key_points": ["<point1>", "<point2>", ...],
  "methodologies": ["<method1>", ...],
  "metrics": ["<metric and value>", ...],
  "limitations": ["<limitation>", ...],
  "exact_quote": "<extract 1-2 key sentences VERBATIM from the text that perfectly captures the main finding>"
}

If a field has no relevant content, return an empty list.
"""


async def _fetch_content(url: str, source_type: str) -> str:
    """Fetch and clean page content. Falls back to empty string on failure."""
    try:
        if source_type == "arxiv":
            headers = {"User-Agent": "AIResearch/1.0 (research tool)"}
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                soup = BeautifulSoup(resp.text, "lxml")
                abstract = soup.find("blockquote", class_="abstract")
                return abstract.get_text(strip=True)[:3000] if abstract else ""
        else:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "AIResearch/1.0"})
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                return " ".join(soup.get_text(separator=" ").split())[:4000]
    except Exception as exc:
        logger.debug("fetch_failed", url=url, error=str(exc))
        return ""


async def _extract_one(source: dict, topic: str, model: OpenRouterModel) -> dict:
    content = await _fetch_content(source["url"], source.get("source_type", "web"))

    if not content:
        content = source.get("snippet", "")

    if not content:
        return {
            "source_url": source["url"],
            "source_title": source["title"],
            "key_points": [],
            "methodologies": [],
            "metrics": [],
            "limitations": [],
            "exact_quote": source.get("snippet", ""),
        }

    try:
        response = await generate_content_with_retry(
            model,
            f"Topic: {topic}\n\nSource: {source['title']}\nContent:\n{content}",
            generation_config=SimpleNamespace(max_output_tokens=512, response_mime_type="application/json"),
        )
        data = extract_json(response.text)
        return {
            "source_url": source["url"],
            "source_title": source["title"],
            **data,
        }
    except Exception as exc:
        logger.debug("extraction_llm_error", url=source["url"], error=str(exc))
        return {
            "source_url": source["url"],
            "source_title": source["title"],
            "key_points": [],
            "methodologies": [],
            "metrics": [],
            "limitations": [],
            "exact_quote": source.get("snippet", ""),
        }


async def extractor_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {}

    log = logger.bind(agent="extractor", report_id=state["report_id"])
    validated_sources = state.get("validated_sources", [])
    log.info("extractor_start", sources=len(validated_sources))

    if not validated_sources:
        return {"error": "No validated sources", "current_agent": "extractor"}

    model = OpenRouterModel(
        model_name=state.get("model", settings.OPENROUTER_MODEL),
        system_instruction=EXTRACTOR_SYSTEM,
    )

    top_sources = validated_sources[:5]

    findings = await asyncio.gather(
        *[_extract_one(s, state["topic"], model) for s in top_sources]
    )

    log.info("extractor_complete", findings=len(findings))
    return {
        "findings": list(findings),
        "current_agent": "extractor",
        "completed_agents": state.get("completed_agents", []) + ["extractor"],
    }
