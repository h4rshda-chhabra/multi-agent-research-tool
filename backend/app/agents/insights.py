import json
import structlog
from types import SimpleNamespace
from app.agents.openrouter_client import OpenRouterModel

from app.config import get_settings
from app.agents.state import ResearchState

logger = structlog.get_logger()
settings = get_settings()

INSIGHTS_SYSTEM = """You are an expert research analyst specializing in meta-analysis of academic literature. Your task is to analyze research findings and produce structured insights about the research landscape.

Given a research topic, validated sources, extracted findings, a synthesized report, and subtopics, you must generate a comprehensive insights object.

Return ONLY a valid JSON object - no markdown fences, no explanation.

Schema:
{
  "research_gaps": ["<open problem or unanswered question 1>", ...],
  "novel_ideas": [
    {"title": "<idea title>", "description": "<brief description>", "feasibility": "high|medium|low"},
    ...
  ],
  "literature_matrix": {
    "columns": ["Paper", "Dataset", "Algorithm", "Key Result", "Limitation"],
    "rows": [
      ["<paper short title>", "<dataset>", "<algorithm/method>", "<key result>", "<limitation>"],
      ...
    ]
  },
  "citation_graph": {
    "nodes": [
      {"id": "<number as string>", "title": "<paper/work title>", "year": <year as int>, "type": "foundational|influential|recent|standard"}
    ],
    "edges": [
      {"from": "<node id>", "to": "<node id>"}
    ]
  },
  "research_timeline": [
    {"year": <year as int>, "event": "<description of milestone>", "paper": "<paper or source title>"},
    ...
  ],
  "contradictions": [
    {
      "topic": "<topic where contradiction exists>",
      "paper_a": {"title": "<paper A title>", "claim": "<claim made by paper A>"},
      "paper_b": {"title": "<paper B title>", "claim": "<claim made by paper B>"},
      "context": "<brief explanation of the contradiction>"
    },
    ...
  ],
  "datasets": [
    {"name": "<dataset name>", "size": "large|medium|small", "domain": "<domain>", "url": "<url or empty string>"},
    ...
  ],
  "reproducibility": [
    {"paper": "<paper title>", "code_available": true|false, "dataset_public": true|false, "score": "high|medium|low", "notes": "<brief notes>"},
    ...
  ],
  "research_questions": ["<open research question 1>?", ...],
  "benchmarks": [
    {"metric": "<metric name>", "best_paper": "<paper that achieves best>", "value": "<value with units>", "context": "<brief context>"},
    ...
  ]
}

Rules:
- Use ONLY information grounded in the provided sources and findings. Do not hallucinate papers or data.
- research_gaps: 3-8 genuine open problems identified from the literature.
- novel_ideas: 3-6 creative but grounded research directions building on the findings.
- literature_matrix: include up to 10 rows, one per key paper/source from the findings.
- citation_graph: nodes are key papers/sources; edges represent "builds on" or "cites" relationships you can infer. Include 5-15 nodes.
- research_timeline: chronological milestones (major papers, techniques, breakthroughs). 5-12 events.
- contradictions: genuine conflicting findings between sources. 0-5 contradictions (omit section as empty array if none found).
- datasets: datasets mentioned or implied by the sources. 3-8 datasets.
- reproducibility: assess each key paper. 5-10 entries.
- research_questions: 4-8 specific, actionable research questions.
- benchmarks: key performance metrics from the field with best-known values. 3-8 benchmarks.
- If you cannot determine a value, use reasonable defaults (empty string for unknown URLs, false for unknown boolean fields, "medium" for unknown size/score).
"""


async def insights_node(state: ResearchState) -> dict:
    log = logger.bind(agent="insights", report_id=state["report_id"])
    log.info("insights_start")

    model = OpenRouterModel(
        model_name=settings.OPENROUTER_MODEL,
        system_instruction=INSIGHTS_SYSTEM,
    )

    # Build a concise prompt with the key research data
    topic = state.get("topic", "")
    subtopics = state.get("subtopics", [])
    validated_sources = state.get("validated_sources", [])
    findings = state.get("findings", [])
    report_markdown = state.get("report_markdown", "")

    # Summarise sources compactly to stay within token limits
    sources_summary = []
    for src in validated_sources[:20]:
        sources_summary.append({
            "title": src.get("title", ""),
            "url": src.get("url", ""),
            "domain": src.get("domain", ""),
            "snippet": src.get("snippet", "")[:300],
            "published_date": src.get("published_date", ""),
            "total_score": src.get("total_score", 0),
        })

    # Summarise findings compactly
    findings_summary = []
    for f in findings[:15]:
        findings_summary.append({
            "source_title": f.get("source_title", ""),
            "source_url": f.get("source_url", ""),
            "key_points": f.get("key_points", [])[:5],
            "methodologies": f.get("methodologies", [])[:3],
            "metrics": f.get("metrics", [])[:3],
            "limitations": f.get("limitations", [])[:3],
        })

    user_msg = f"""Research Topic: {topic}

Subtopics: {json.dumps(subtopics)}

Validated Sources ({len(sources_summary)} of {len(validated_sources)}):
{json.dumps(sources_summary, indent=2)}

Extracted Findings ({len(findings_summary)} of {len(findings)}):
{json.dumps(findings_summary, indent=2)}

Synthesized Report (first 3000 chars):
{report_markdown[:3000]}

Generate comprehensive research insights for this topic based strictly on the above data.
"""

    try:
        response = await model.generate_content_async(
            user_msg,
            generation_config=SimpleNamespace(max_output_tokens=8192, response_mime_type="application/json"),
        )

        raw = response.text.strip()
        # Strip markdown fences if model adds them anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)

        log.info("insights_complete", keys=list(data.keys()))
        return {
            "insights": data,
            "current_agent": "insights",
            "completed_agents": state.get("completed_agents", []) + ["insights"],
        }

    except Exception as exc:
        log.error("insights_error", error=str(exc))
        return {
            "error": f"Insights generation failed: {exc}",
            "current_agent": "insights",
        }
