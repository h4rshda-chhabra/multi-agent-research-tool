import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.saved_report import SavedReport
from app.models.user import User
from app.schemas.research import ResearchRequest, ResearchStartResponse
from app.schemas.report import ReportOut
from app.services.research_service import run_research, stream_progress

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchStartResponse, status_code=202)
async def start_research(
    body: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    report = Report(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        topic=body.topic,
        status="running",
    )
    db.add(report)
    await db.commit()

    background_tasks.add_task(run_research, report.id, body.topic, current_user.id)

    return ResearchStartResponse(
        report_id=report.id,
        status="running",
        message="Research pipeline started",
    )


@router.get("/{report_id}/stream")
async def research_stream(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Report not found")

    return StreamingResponse(
        stream_progress(report_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.sources), selectinload(Report.agent_runs))
        .where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    saved = await db.execute(
        select(SavedReport).where(
            SavedReport.user_id == current_user.id,
            SavedReport.report_id == report_id,
        )
    )
    is_saved = saved.scalar_one_or_none() is not None

    out = ReportOut.model_validate(report)
    out.is_saved = is_saved
    return out
