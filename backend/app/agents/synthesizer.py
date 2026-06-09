import structlog
import google.generativeai as genai

from app.config import get_settings
from app.agents.state import ResearchState
from app.agents.utils import generate_content_with_retry

logger = structlog.get_logger()
settings = get_settings()

SYNTHESIZER_SYSTEM = """You are a world-class research writer. Synthesize the provided research findings into a comprehensive, well-structured academic report in Markdown.

Structure the report with these exact sections in order:

# {topic}

## Executive Summary
## Introduction
## Core Concepts
## Literature Review
## Methodologies
## Benchmarks & Metrics
## Comparison Table (use Markdown table)
## Applications
## Limitations & Challenges
## Future Directions
## References

Guidelines:
- Write in a professional, academic tone.
- Use inline citations like [1], [2], etc., mapped to the References section.
- The Comparison Table should compare key approaches, methods, or tools.
- References section must list all cited sources with their titles and URLs.
- Minimum 1500 words total.
- Do NOT include a preamble - start directly with the H1 heading.
"""


async def synthesizer_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {}

    log = logger.bind(agent="synthesizer", report_id=state["report_id"])
    log.info("synthesizer_start")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYNTHESIZER_SYSTEM.format(topic=state["topic"]),
    )

    findings = state.get("findings", [])
    validated_sources = state.get("validated_sources", [])

    refs = []
    for i, s in enumerate(validated_sources, 1):
        refs.append(f"[{i}] {s['title']} - {s['url']}")

    findings_text = ""
    for f in findings:
        findings_text += f"\n\n### {f['source_title']}\n"
        if f.get("key_points"):
            findings_text += "Key Points:\n" + "\n".join(f"- {p}" for p in f["key_points"]) + "\n"
        if f.get("methodologies"):
            findings_text += "Methodologies:\n" + "\n".join(f"- {m}" for m in f["methodologies"]) + "\n"
        if f.get("metrics"):
            findings_text += "Metrics:\n" + "\n".join(f"- {m}" for m in f["metrics"]) + "\n"
        if f.get("limitations"):
            findings_text += "Limitations:\n" + "\n".join(f"- {l}" for l in f["limitations"]) + "\n"

    user_message = (
        f"Topic: {state['topic']}\n"
        f"Subtopics: {', '.join(state.get('subtopics', []))}\n"
        f"Research Direction: {state.get('research_direction', '')}\n\n"
        f"Extracted Findings:{findings_text}\n\n"
        f"Available References:\n" + "\n".join(refs)
    )

    try:
        response = await generate_content_with_retry(
            model,
            user_message,
            generation_config=genai.types.GenerationConfig(max_output_tokens=6000),
        )

        markdown = response.text.strip()
        log.info("synthesizer_complete", chars=len(markdown))
        return {
            "report_markdown": markdown,
            "current_agent": "synthesizer",
            "completed_agents": state.get("completed_agents", []) + ["synthesizer"],
        }

    except Exception as exc:
        log.error("synthesizer_error", error=str(exc))
        return {"error": f"Synthesizer failed: {exc}", "current_agent": "synthesizer"}
