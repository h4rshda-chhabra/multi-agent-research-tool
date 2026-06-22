import structlog
from types import SimpleNamespace
# OpenRouter integration
from app.agents.openrouter_client import OpenRouterModel

from app.config import get_settings
from app.agents.state import ResearchState
from app.agents.utils import generate_content_with_retry, extract_json

logger = structlog.get_logger()
settings = get_settings()

PLANNER_SYSTEM = """You are an expert academic research planner. Your job is to decompose a research topic into targeted search queries and subtopics.

Return ONLY a valid JSON object - no markdown fences, no explanation. Schema:
{
  "topic": "<refined topic string>",
  "queries": ["<query1>", ...],
  "subtopics": ["<subtopic1>", ...],
  "research_direction": "<one sentence describing the research approach>"
}

Rules:
- Generate exactly 4 diverse queries (definitions, implementations, benchmarks, comparisons, limitations, recent advances).
- Each query should be distinct and suitable for academic/web search.
- Subtopics: 2-3 key subtopics that compose the topic.
"""


async def planner_node(state: ResearchState) -> dict:
    log = logger.bind(agent="planner", report_id=state["report_id"])
    log.info("planner_start")

    # Configuration handled by OpenRouterModel
    model = OpenRouterModel(
        model_name=state.get("model", settings.OPENROUTER_MODEL),
        system_instruction=PLANNER_SYSTEM,
    )

    try:
        response = await generate_content_with_retry(
            model,
            f"Research topic: {state['topic']}",
            generation_config=SimpleNamespace(
                max_output_tokens=512,
                response_mime_type="application/json",
            ),
        )

        data = extract_json(response.text)

        log.info("planner_complete", queries=len(data.get("queries", [])))
        return {
            "queries": data.get("queries", []),
            "subtopics": data.get("subtopics", []),
            "research_direction": data.get("research_direction", ""),
            "current_agent": "planner",
            "completed_agents": state.get("completed_agents", []) + ["planner"],
        }

    except Exception as exc:
        log.error("planner_error", error=str(exc))
        return {
            "error": f"Planner failed: {exc}",
            "current_agent": "planner",
        }
