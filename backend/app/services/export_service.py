"""PDF and Markdown export for completed reports."""
import io
import markdown as md_lib

from app.models.report import Report


def export_markdown(report: Report) -> bytes:
    content = report.markdown_content or ""
    return content.encode("utf-8")


def export_pdf(report: Report) -> bytes:
    """Convert markdown report to PDF via WeasyPrint."""
    try:
        from weasyprint import HTML, CSS

        content = report.markdown_content or ""
        html_body = md_lib.markdown(content, extensions=["tables", "fenced_code", "codehilite"])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; line-height: 1.7; color: #1a1a2e; }}
  h1 {{ color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 8px; }}
  h2 {{ color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 32px; }}
  h3 {{ color: #16213e; }}
  a {{ color: #0f3460; }}
  pre {{ background: #f4f4f4; padding: 16px; border-radius: 4px; overflow-x: auto; font-size: 0.85em; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th {{ background: #0f3460; color: white; padding: 10px; text-align: left; }}
  td {{ padding: 8px 10px; border: 1px solid #ddd; }}
  tr:nth-child(even) {{ background: #f9f9f9; }}
  blockquote {{ border-left: 4px solid #e94560; margin: 0; padding: 0 16px; color: #555; }}
</style>
</head>
<body>{html_body}</body>
</html>"""

        return HTML(string=html).write_pdf()

    except ImportError:
        # WeasyPrint not installed — return HTML as fallback
        return html.encode("utf-8")
