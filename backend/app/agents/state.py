from typing import TypedDict, Optional
from dataclasses import dataclass, field


@dataclass
class SourceResult:
    url: str
    title: str
    domain: str
    snippet: str
    published_date: str
    source_type: str  # "web" | "arxiv"
    authors: list[str] = field(default_factory=list)
    doi: str = ""


@dataclass
class ValidatedSource:
    url: str
    title: str
    domain: str
    snippet: str
    published_date: str
    source_type: str
    relevance_score: float
    credibility_score: float
    recency_score: float
    technical_depth_score: float
    total_score: float
    authors: list[str] = field(default_factory=list)
    doi: str = ""


@dataclass
class Finding:
    source_url: str
    source_title: str
    key_points: list[str] = field(default_factory=list)
    methodologies: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    exact_quote: str = ""


class ResearchState(TypedDict):
    report_id: str
    user_id: str
    topic: str

    # Planner outputs
    queries: list[str]
    subtopics: list[str]
    research_direction: str

    # Search outputs
    raw_sources: list[dict]   # serialised SourceResult dicts

    # Validator outputs
    validated_sources: list[dict]  # serialised ValidatedSource dicts

    # Extractor outputs
    findings: list[dict]  # serialised Finding dicts

    # Synthesizer outputs
    report_markdown: str

    # Insights outputs
    insights: Optional[dict]

    # Meta
    current_agent: str
    completed_agents: list[str]
    error: Optional[str]
