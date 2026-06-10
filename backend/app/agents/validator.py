import json
import structlog
from types import SimpleNamespace
from app.agents.openrouter_client import OpenRouterModel

from app.config import get_settings
from app.agents.state import ResearchState
from app.agents.utils import generate_content_with_retry

logger = structlog.get_logger()
settings = get_settings()

HIGH_CRED_DOMAINS = {
    "arxiv.org", "ieee.org", "ieeexplore.ieee.org", "acm.org", "dl.acm.org",
    "nature.com", "science.org", "proceedings.neurips.cc", "icml.cc",
    "aclanthology.org", "semanticscholar.org",
}
MEDIUM_CRED_DOMAINS = {
    "github.com", "openai.com", "anthropic.com", "deepmind.com",
    "huggingface.co", "paperswithcode.com", "distill.pub", "research.google",
}

VALIDATOR_SYSTEM = """You are a research quality analyst. Score each source and return ONLY valid JSON.

For each source, output scores between 0.0 and 10.0:
- relevance: how directly relevant to the research topic
- recency: how recent (prefer ≤2 years old; penalise >5 years)
- technical_depth: depth of technical content

Return ONLY this JSON structure (no markdown, no explanation):
{
  "scores": [
    {"url": "<url>", "relevance": 8.5, "recency": 9.0, "technical_depth": 7.0},
    ...
  ]
}
"""


async def validator_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {}

    log = logger.bind(agent="validator", report_id=state["report_id"])
    raw_sources = state.get("raw_sources", [])
    log.info("validator_start", sources=len(raw_sources))

    if not raw_sources:
        return {"error": "No sources to validate", "current_agent": "validator"}

    # Configuration handled by OpenRouterModel
    model = OpenRouterModel(
        model_name=settings.OPENROUTER_MODEL,
        system_instruction=VALIDATOR_SYSTEM,
    )

    compact = [
        {"url": s["url"], "title": s["title"], "snippet": s["snippet"][:200], "date": s.get("published_date", "")}
        for s in raw_sources
    ]

    try:
        response = await generate_content_with_retry(
            model,
            f"Research topic: {state['topic']}\n\nSources:\n{json.dumps(compact, indent=2)}",
            generation_config=SimpleNamespace(max_output_tokens=2048, response_mime_type="application/json"),
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        score_map: dict[str, dict] = {item["url"]: item for item in data.get("scores", [])}

    except Exception as exc:
        log.warning("validator_llm_error", error=str(exc))
        score_map = {}

    validated = []
    for s in raw_sources:
        url = s["url"]
        domain = s.get("domain", "")
        llm = score_map.get(url, {})

        relevance = float(llm.get("relevance", 5.0))
        recency = float(llm.get("recency", 5.0))
        technical_depth = float(llm.get("technical_depth", 5.0))

        if domain in HIGH_CRED_DOMAINS:
            credibility = 9.5
        elif domain in MEDIUM_CRED_DOMAINS:
            credibility = 7.5
        else:
            credibility = 5.0

        total = (relevance * 0.35 + credibility * 0.30 + recency * 0.15 + technical_depth * 0.20)

        validated.append({
            **s,
            "relevance_score": round(relevance, 2),
            "credibility_score": round(credibility, 2),
            "recency_score": round(recency, 2),
            "technical_depth_score": round(technical_depth, 2),
            "total_score": round(total, 2),
        })

    validated.sort(key=lambda x: x["total_score"], reverse=True)
    top = [v for v in validated if v["total_score"] >= 4.5][:12]

    log.info("validator_complete", kept=len(top))
    return {
        "validated_sources": top,
        "current_agent": "validator",
        "completed_agents": state.get("completed_agents", []) + ["validator"],
    }
