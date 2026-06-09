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


def _slug(topic: str) -> str:
    return topic[:40].replace(" ", "-").lower()


def _build_response(report: Report, fmt: str) -> Response:
    """Generate and return the export Response for the given format."""
    slug = _slug(report.topic)

    if fmt == "markdown":
        content = export_markdown(report)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{slug}.md"'},
        )

    if fmt == "pdf":
        try:
            content, mime_type = export_pdf(report)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

        # If WeasyPrint/fpdf2 both failed, export_pdf returns HTML; adjust extension.
        ext = "pdf" if mime_type == "application/pdf" else "html"
        return Response(
            content=content,
            media_type=mime_type,
            headers={"Content-Disposition": f'attachment; filename="{slug}.{ext}"'},
        )

    raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'markdown'")


# ── POST endpoint (axios / programmatic use) ─────────────────────────────────

@router.post("")
async def export_report_post(
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

    return _build_response(report, body.format)


# ── GET endpoint (direct browser download, token in query param) ─────────────
# Used by the frontend anchor-tag / window.open approach to avoid the
# XMLHttpRequest CORS restriction on cross-origin blob downloads.

@router.get("")
async def export_report_get(
    report_id: str,
    format: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "complete":
        raise HTTPException(status_code=400, detail="Report not yet complete")

    return _build_response(report, format)
