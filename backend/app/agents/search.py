import asyncio
import structlog
from dataclasses import asdict
from urllib.parse import urlparse

import arxiv
from tavily import TavilyClient

from app.config import get_settings
from app.agents.state import ResearchState, SourceResult

logger = structlog.get_logger()
settings = get_settings()

TRUSTED_DOMAINS = {
    "arxiv.org", "ieee.org", "ieeexplore.ieee.org", "acm.org", "dl.acm.org",
    "github.com", "openai.com", "anthropic.com", "deepmind.com", "huggingface.co",
    "proceedings.neurips.cc", "icml.cc", "aclanthology.org", "paperswithcode.com",
    "nature.com", "science.org", "springer.com", "semanticscholar.org",
    "towardsdatascience.com", "ai.googleblog.com", "research.google",
    "blogs.microsoft.com", "distill.pub",
}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return ""


async def _tavily_search(query: str, api_key: str | None = None) -> list[SourceResult]:
    try:
        client = TavilyClient(api_key=api_key or settings.TAVILY_API_KEY)
        response = await asyncio.to_thread(
            client.search,
            query=query,
            max_results=5,
            include_answer=False,
            search_depth="advanced",
        )
        results = []
        for r in response.get("results", []):
            domain = _domain(r.get("url", ""))
            results.append(
                SourceResult(
                    url=r.get("url", ""),
                    title=r.get("title", "Untitled"),
                    domain=domain,
                    snippet=r.get("content", "")[:500],
                    published_date=r.get("published_date", ""),
                    source_type="web",
                    authors=[],
                    doi="",
                )
            )
        return results
    except Exception as exc:
        logger.warning("tavily_search_error", query=query, error=str(exc))
        return []


async def _arxiv_search(query: str) -> list[SourceResult]:
    try:
        search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
        results = []
        for paper in await asyncio.to_thread(list, search.results()):
            results.append(
                SourceResult(
                    url=paper.entry_id,
                    title=paper.title,
                    domain="arxiv.org",
                    snippet=paper.summary[:500],
                    published_date=str(paper.published.date()) if paper.published else "",
                    source_type="arxiv",
                    authors=[a.name for a in paper.authors],
                    doi=paper.doi if paper.doi else "",
                )
            )
        return results
    except Exception as exc:
        logger.warning("arxiv_search_error", query=query, error=str(exc))
        return []


async def search_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {}

    log = logger.bind(agent="search", report_id=state["report_id"])
    log.info("search_start", queries=len(state.get("queries", [])))

    queries = state.get("queries", [])
    if not queries:
        return {"error": "No queries from planner", "current_agent": "search"}

    # Run all queries concurrently; rotate Tavily keys across queries
    tavily_keys = settings.tavily_keys
    tasks = []
    for i, q in enumerate(queries):
        key = tavily_keys[i % len(tavily_keys)]
        tasks.append(_tavily_search(q, api_key=key))
        tasks.append(_arxiv_search(q))

    all_results = await asyncio.gather(*tasks)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique: list[SourceResult] = []
    for batch in all_results:
        for source in batch:
            if source.url and source.url not in seen_urls:
                seen_urls.add(source.url)
                unique.append(source)

    log.info("search_complete", sources=len(unique))
    return {
        "raw_sources": [asdict(s) for s in unique],
        "current_agent": "search",
        "completed_agents": state.get("completed_agents", []) + ["search"],
    }
