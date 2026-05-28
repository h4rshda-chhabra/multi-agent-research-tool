from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ExportRequest
from app.services.export_service import export_markdown, export_pdf

router = APIRouter(prefix="/export", tags=["export"])


@router.post("")
async def export_report(
    body: ExportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report).where(Report.id == body.report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "complete":
        raise HTTPException(status_code=400, detail="Report not yet complete")

    slug = report.topic[:40].replace(" ", "-").lower()

    if body.format == "markdown":
        content = export_markdown(report)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{slug}.md"'},
        )

    if body.format == "pdf":
        content = export_pdf(report)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{slug}.pdf"'},
        )

    raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'markdown'")
