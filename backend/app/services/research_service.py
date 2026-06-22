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
from app.config import get_settings

logger = structlog.get_logger()

# In-memory SSE queues: report_id → asyncio.Queue
_progress_queues: dict[str, asyncio.Queue] = {}

# Cancellation signals: report_id → asyncio.Event
_cancel_events: dict[str, asyncio.Event] = {}

# Active research runs (cleared on finish/error/cancel)
_active_runs: set[str] = set()

# Canonical pipeline order (must match graph.py)
AGENT_ORDER = ["planner", "search", "validator", "extractor", "synthesizer", "insights"]

AGENT_LABELS = {
    "planner": "Planning Research Strategy",
    "search": "Searching Sources",
    "validator": "Validating Sources",
    "extractor": "Extracting Findings",
    "synthesizer": "Generating Report",
    "insights": "Generating Insights",
}


def cancel_research(report_id: str) -> bool:
    """Signal cancellation for a running research task. Returns True if found."""
    event = _cancel_events.get(report_id)
    if event is None:
        return False
    event.set()
    return True


def _cleanup_cancel(report_id: str) -> None:
    _cancel_events.pop(report_id, None)


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
    now = datetime.now(timezone.utc).replace(tzinfo=None)

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


async def _emit(queue: asyncio.Queue, event: dict) -> None:
    """Put an event on the queue and log it."""
    logger.debug("sse_emit", event_type=event.get("type"), agent=event.get("agent"))
    await queue.put(event)


async def run_research(report_id: str, topic: str, user_id: str, model: str | None = None) -> None:
    """Background task: run the LangGraph pipeline and stream SSE progress events."""
    queue = get_or_create_queue(report_id)
    cancel_event = asyncio.Event()
    _cancel_events[report_id] = cancel_event
    _active_runs.add(report_id)
    log = logger.bind(report_id=report_id)
    log.info("research_start", topic=topic)

    async with AsyncSessionLocal() as db:
        state: ResearchState = {
            "report_id": report_id,
            "user_id": user_id,
            "topic": topic,
            "model": model or get_settings().OPENROUTER_MODEL,
            "queries": [],
            "subtopics": [],
            "research_direction": "",
            "raw_sources": [],
            "validated_sources": [],
            "findings": [],
            "report_markdown": "",
            "insights": None,
            "current_agent": "",
            "completed_agents": [],
            "error": None,
        }

        try:
            # Signal that the first agent (planner) is starting.
            # This allows SSE consumers that connect immediately to show the
            # correct running state without waiting for the first completion event.
            await _emit(queue, {
                "type": "agent_start",
                "agent": "planner",
                "message": AGENT_LABELS["planner"],
                "report_id": report_id,
            })
            await _update_agent_run(db, report_id, "planner", "running")

            async for event in research_graph.astream(state):
                node_name = list(event.keys())[0]
                state_delta = event[node_name]

                log.debug("node_event", node=node_name, keys=list(state_delta.keys()))

                if state_delta.get("error"):
                    log.error("agent_failed", node=node_name, error=state_delta["error"])
                    await _emit(queue, {
                        "type": "agent_error",
                        "agent": node_name,
                        "message": state_delta["error"],
                        "report_id": report_id,
                    })
                    await _update_agent_run(db, report_id, node_name, "failed", error=state_delta["error"])
                    result = await db.execute(select(Report).where(Report.id == report_id))
                    report = result.scalar_one_or_none()
                    if report:
                        report.status = "failed"
                        report.error_message = state_delta["error"]
                        await db.commit()
                    await _emit(queue, {
                        "type": "error",
                        "message": state_delta["error"],
                        "report_id": report_id,
                    })
                    return

                state.update(state_delta)

                # Check for cancellation signal between nodes
                if cancel_event.is_set():
                    log.info("research_cancelled", after_node=node_name)
                    await _update_agent_run(db, report_id, node_name, "cancelled")
                    result = await db.execute(select(Report).where(Report.id == report_id))
                    report = result.scalar_one_or_none()
                    if report:
                        report.status = "cancelled"
                        report.error_message = "Research cancelled by user"
                        await db.commit()
                    await _emit(queue, {
                        "type": "cancelled",
                        "message": "Research cancelled",
                        "report_id": report_id,
                    })
                    return

                label = AGENT_LABELS.get(node_name, node_name)
                await _emit(queue, {
                    "type": "agent_complete",
                    "agent": node_name,
                    "message": f"{label} complete",
                    "report_id": report_id,
                })
                await _update_agent_run(
                    db, report_id, node_name, "complete",
                    output_json=json.dumps({"keys": list(state_delta.keys())}),
                )

                # Emit start event for the next agent so the frontend can
                # immediately reflect the new running state without waiting for
                # the next completion event (important for late SSE connections).
                try:
                    idx = AGENT_ORDER.index(node_name)
                    if idx < len(AGENT_ORDER) - 1:
                        next_agent = AGENT_ORDER[idx + 1]
                        await _emit(queue, {
                            "type": "agent_start",
                            "agent": next_agent,
                            "message": AGENT_LABELS.get(next_agent, next_agent),
                            "report_id": report_id,
                        })
                        await _update_agent_run(db, report_id, next_agent, "running")
                except ValueError:
                    pass  # node_name not in AGENT_ORDER (e.g. custom nodes)

            # Persist validated sources
            for src in state.get("validated_sources", []):
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
                    authors="; ".join(src.get("authors", [])),
                    doi=src.get("doi", ""),
                )
                db.add(source)

            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = "complete"
                report.markdown_content = state.get("report_markdown", "")
                await db.commit()

            await _emit(queue, {"type": "complete", "message": "Report ready", "report_id": report_id})
            log.info("research_complete")

        except Exception as exc:
            log.error("research_pipeline_error", error=str(exc), exc_info=True)
            await _emit(queue, {"type": "error", "message": str(exc), "report_id": report_id})
            # Use a fresh session for error recovery in case the original session is dirty
            async with AsyncSessionLocal() as db2:
                result = await db2.execute(select(Report).where(Report.id == report_id))
                report = result.scalar_one_or_none()
                if report:
                    report.status = "failed"
                    report.error_message = str(exc)
                    await db2.commit()
        finally:
            _active_runs.discard(report_id)
            # Give the SSE consumer time to drain the terminal event before
            # we destroy the queue. The StreamingResponse generator breaks its
            # loop on complete/error/cancelled, so 5 s is ample.
            await asyncio.sleep(5)
            _cleanup_queue(report_id)
            _cleanup_cancel(report_id)
            log.debug("research_cleanup_done")


async def stream_progress(report_id: str) -> AsyncGenerator[str, None]:
    """SSE generator: yields data: {...}\n\n until complete/error."""
    # If no active run exists for this report it's already done — tell the
    # frontend immediately so the optimistic "planner running" state clears.
    if report_id not in _active_runs:
        yield f"data: {json.dumps({'type': 'complete', 'message': 'Report ready', 'report_id': report_id})}\n\n"
        return

    queue = get_or_create_queue(report_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping', 'report_id': report_id})}\n\n"
                continue

            yield f"data: {json.dumps(event)}\n\n"

            if event.get("type") in ("complete", "error", "cancelled"):
                break
    except asyncio.CancelledError:
        pass
