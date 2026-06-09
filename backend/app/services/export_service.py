"""PDF and Markdown export for completed reports."""
import markdown as md_lib
import structlog

from app.models.report import Report

logger = structlog.get_logger()

_EXPORT_CSS = """
  body { font-family: Georgia, serif; max-width: 800px; margin: 40px auto;
         line-height: 1.7; color: #1a1a2e; }
  h1 { color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 8px; }
  h2 { color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 32px; }
  h3 { color: #16213e; }
  a  { color: #0f3460; }
  pre { background: #f4f4f4; padding: 16px; border-radius: 4px;
        overflow-x: auto; font-size: 0.85em; }
  code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  th { background: #0f3460; color: white; padding: 10px; text-align: left; }
  td { padding: 8px 10px; border: 1px solid #ddd; }
  tr:nth-child(even) { background: #f9f9f9; }
  blockquote { border-left: 4px solid #e94560; margin: 0; padding: 0 16px; color: #555; }
"""


def _html_document(html_body: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang='en'>\n"
        f"<head><meta charset='utf-8'><style>{_EXPORT_CSS}</style></head>\n"
        f"<body>{html_body}</body>\n</html>"
    )


def export_markdown(report: Report) -> bytes:
    return (report.markdown_content or "").encode("utf-8")


def export_pdf(report: Report) -> tuple[bytes, str]:
    """Return (content_bytes, mime_type).

    Tries WeasyPrint → fpdf2 → HTML fallback in order.
    Always returns something downloadable rather than raising.
    """
    content = report.markdown_content or ""

    # Render markdown to HTML once (used by both WeasyPrint and HTML fallback)
    html_body = md_lib.markdown(
        content, extensions=["tables", "fenced_code", "codehilite"]
    )
    html_doc = _html_document(html_body)

    # ── 1. WeasyPrint (best quality; needs GTK on Windows) ───────────────────
    try:
        from weasyprint import HTML  # type: ignore

        pdf_bytes = HTML(string=html_doc).write_pdf()
        logger.info("export_pdf_weasyprint")
        return pdf_bytes, "application/pdf"
    except Exception as wp_err:
        logger.warning("weasyprint_unavailable", error=str(wp_err))

    # ── 2. fpdf2 (pure Python, no external DLLs; Windows-compatible) ─────────
    try:
        pdf_bytes = _fpdf2_pdf(content)
        logger.info("export_pdf_fpdf2")
        return pdf_bytes, "application/pdf"
    except Exception as fp_err:
        logger.warning("fpdf2_failed", error=str(fp_err))

    # ── 3. Styled HTML fallback (user can File → Print → Save as PDF) ────────
    logger.info("export_pdf_html_fallback")
    return html_doc.encode("utf-8"), "text/html"


def _fpdf2_pdf(markdown_content: str) -> bytes:
    """Convert markdown → PDF via fpdf2 (no external dependencies)."""
    from fpdf import FPDF  # type: ignore

    # Use simpler extensions for fpdf2's limited HTML parser
    html_body = md_lib.markdown(markdown_content, extensions=["tables", "fenced_code"])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.write_html(html_body)
    return bytes(pdf.output())
