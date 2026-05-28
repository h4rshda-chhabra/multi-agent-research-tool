"""
Orchestrates the LangGraph research workflow.
Streams progress events into per-report asyncio.Queues for SSE consumption.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import research_graph
from app.agents.state import ResearchState
from app.database import AsyncSessionLocal
from app.models.agent_run import AgentRun
from app.models.report import Report
from app.models.source import Source

logger = structlog.get_logger()

# In-memory SSE queues: report_id → asyncio.Queue
_progress_queues: dict[str, asyncio.Queue] = {}

AGENT_LABELS = {
    "planner": "Planning Research Strategy",
    "search": "Searching Sources",
    "validator": "Validating Sources",
    "extractor": "Extracting Findings",
    "synthesizer": "Generating Report",
}


def get_or_create_queue(report_id: str) -> asyncio.Queue:
    if report_id not in _progress_queues:
        _progress_queues[report_id] = asyncio.Queue()
    return _progress_queues[report_id]


def _cleanup_queue(report_id: str) -> None:
    _progress_queues.pop(report_id, None)


async def _update_agent_run(
    db: AsyncSession,
    report_id: str,
    agent_name: str,
    status: str,
    output_json: str | None = None,
    error: str | None = None,
) -> None:
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.report_id == report_id, AgentRun.agent_name == agent_name
        )
    )
    run = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if run is None:
        run = AgentRun(
            id=str(uuid.uuid4()),
            report_id=report_id,
            agent_name=agent_name,
            status=status,
            started_at=now,
        )
        db.add(run)
    else:
        run.status = status
        if status in ("complete", "failed"):
            run.completed_at = now
        if output_json:
            run.output_json = output_json
        if error:
            run.error = error

    await db.commit()


async def run_research(report_id: str, topic: str, user_id: str) -> None:
    """Background task: run the graph and stream progress events."""
    queue = get_or_create_queue(report_id)
    log = logger.bind(report_id=report_id)

    async with AsyncSessionLocal() as db:
        initial_state: ResearchState = {
            "report_id": report_id,
            "user_id": user_id,
            "topic": topic,
            "queries": [],
            "subtopics": [],
            "research_direction": "",
            "raw_sources": [],
            "validated_sources": [],
            "findings": [],
            "report_markdown": "",
            "current_agent": "",
            "completed_agents": [],
            "error": None,
        }

        try:
            async for event in research_graph.astream(initial_state):
                node_name = list(event.keys())[0]
                state_delta = event[node_name]

                if state_delta.get("error"):
                    await queue.put({
                        "type": "agent_error",
                        "agent": node_name,
                        "message": state_delta["error"],
                        "report_id": report_id,
                    })
                    await _update_agent_run(db, report_id, node_name, "failed", error=state_delta["error"])
                    # Update report status to failed
                    result = await db.execute(select(Report).where(Report.id == report_id))
                    report = result.scalar_one_or_none()
                    if report:
                        report.status = "failed"
                        report.error_message = state_delta["error"]
                        await db.commit()
                    await queue.put({"type": "error", "message": state_delta["error"], "report_id": report_id})
                    return

                label = AGENT_LABELS.get(node_name, node_name)
                await queue.put({
                    "type": "agent_complete",
                    "agent": node_name,
                    "message": f"{label} complete",
                    "report_id": report_id,
                })
                await _update_agent_run(
                    db, report_id, node_name, "complete",
                    output_json=json.dumps({"keys": list(state_delta.keys())})
                )

            # Retrieve final state by running once more (astream gives deltas)
            final = await research_graph.ainvoke(initial_state)

            # Persist sources
            for src in final.get("validated_sources", []):
                source = Source(
                    id=str(uuid.uuid4()),
                    report_id=report_id,
                    url=src["url"],
                    title=src["title"],
                    domain=src.get("domain", ""),
                    snippet=src.get("snippet", ""),
                    published_date=src.get("published_date", ""),
                    relevance_score=src.get("relevance_score", 0.0),
                    credibility_score=src.get("credibility_score", 0.0),
                    recency_score=src.get("recency_score", 0.0),
                    technical_depth_score=src.get("technical_depth_score", 0.0),
                    total_score=src.get("total_score", 0.0),
                )
                db.add(source)

            # Update report
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = "complete"
                report.markdown_content = final.get("report_markdown", "")
                await db.commit()

            await queue.put({"type": "complete", "message": "Report ready", "report_id": report_id})
            log.info("research_complete")

        except Exception as exc:
            log.error("research_pipeline_error", error=str(exc))
            await queue.put({"type": "error", "message": str(exc), "report_id": report_id})
            async with AsyncSessionLocal() as db2:
                result = await db2.execute(select(Report).where(Report.id == report_id))
                report = result.scalar_one_or_none()
                if report:
                    report.status = "failed"
                    report.error_message = str(exc)
                    await db2.commit()
        finally:
            # Give SSE consumer 5 s to drain, then clean up
            await asyncio.sleep(5)
            _cleanup_queue(report_id)


async def stream_progress(report_id: str) -> AsyncGenerator[str, None]:
    """SSE generator: yields data: {...}\n\n until complete/error."""
    queue = get_or_create_queue(report_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping', 'report_id': report_id})}\n\n"
                continue

            yield f"data: {json.dumps(event)}\n\n"

            if event.get("type") in ("complete", "error"):
                break
    except asyncio.CancelledError:
        pass
