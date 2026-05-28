import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.saved_report import SavedReport
from app.models.user import User
from app.schemas.report import ReportListItem, SaveReportRequest

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(50)
    )
    reports = result.scalars().all()

    saved_result = await db.execute(
        select(SavedReport.report_id).where(SavedReport.user_id == current_user.id)
    )
    saved_ids = {row[0] for row in saved_result.all()}

    items = []
    for r in reports:
        item = ReportListItem.model_validate(r)
        item.is_saved = r.id in saved_ids
        items.append(item)
    return items


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
    await db.commit()


@router.get("/saved", response_model=list[ReportListItem])
async def list_saved(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report)
        .join(SavedReport, SavedReport.report_id == Report.id)
        .where(SavedReport.user_id == current_user.id)
        .order_by(SavedReport.saved_at.desc())
    )
    reports = result.scalars().all()
    items = [ReportListItem.model_validate(r) for r in reports]
    for item in items:
        item.is_saved = True
    return items


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_report(
    body: SaveReportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exists = await db.execute(
        select(Report).where(Report.id == body.report_id, Report.user_id == current_user.id)
    )
    if not exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Report not found")

    already = await db.execute(
        select(SavedReport).where(
            SavedReport.user_id == current_user.id,
            SavedReport.report_id == body.report_id,
        )
    )
    if already.scalar_one_or_none():
        return {"message": "Already saved"}

    saved = SavedReport(id=str(uuid.uuid4()), user_id=current_user.id, report_id=body.report_id)
    db.add(saved)
    await db.commit()
    return {"message": "Report saved"}


@router.delete("/save/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(
        delete(SavedReport).where(
            SavedReport.user_id == current_user.id,
            SavedReport.report_id == report_id,
        )
    )
    await db.commit()
