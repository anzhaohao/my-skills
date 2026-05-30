from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _img_to_b64(path: str) -> str:
    """Convert image file to base64 data URI for HTML embedding."""
    if not path or not Path(path).exists():
        return ""
    data = Path(path).read_bytes()
    ext = Path(path).suffix.lower().replace(".", "")
    mime = "image/png" if ext == "png" else f"image/{ext}"
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _resolve_template_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def _resolve_static_dir() -> Path:
    return Path(__file__).resolve().parent / "static"


def render_print_html(report: dict, result: dict, generated_at: str,
                      output_path: Path) -> Path:
    """Render the complete print-ready HTML report."""
    template_dir = _resolve_template_dir()
    static_dir = _resolve_static_dir()

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report_template.html")

    # Read CSS
    report_css = ""
    report_css_path = static_dir / "report.css"
    if report_css_path.exists():
        report_css = report_css_path.read_text(encoding="utf-8")

    print_css = ""
    print_css_path = static_dir / "print.css"
    if print_css_path.exists():
        print_css = print_css_path.read_text(encoding="utf-8")

    # Embed chart images as base64
    chart_b64 = {}
    for key, path in report.get("chart_paths", {}).items():
        b64 = _img_to_b64(path)
        if b64:
            chart_b64[key] = b64

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = template.render(
        report=report,
        result=result,
        chart_images=chart_b64,
        generated_at=generated_at,
        report_css=report_css,
        print_css=print_css,
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path


def export_pdf_playwright(html_path: Path, pdf_path: Path) -> bool:
    """Use Playwright to convert HTML to PDF. Returns True on success."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{html_path.as_posix()}", wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "18mm", "bottom": "18mm",
                        "left": "18mm", "right": "18mm"},
            )
            browser.close()
        return True
    except Exception:
        return False


def export_pdf(
    report: dict,
    result: dict,
    output_dir: Path,
    pdf_filename: str = "",
) -> dict:
    """Export the complete PDF report.

    Returns dict with status info: {pdf, print_html, ok, message}
    """
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_filename:
        date_part = time.strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"教学质量分析报告_{date_part}.pdf"

    html_path = output_dir / "print_report.html"
    pdf_path = output_dir / pdf_filename

    # Step 1: Render HTML
    render_print_html(report, result, generated_at, html_path)

    # Step 2: Try Playwright PDF
    if export_pdf_playwright(html_path, pdf_path):
        return {
            "pdf": str(pdf_path),
            "print_html": str(html_path),
            "ok": True,
            "message": "PDF 报告已生成。",
        }

    # Step 3: Fallback - keep HTML for manual printing
    return {
        "pdf": "",
        "print_html": str(html_path),
        "ok": False,
        "message": (
            "Playwright 不可用，无法自动生成 PDF。"
            "已保留完整 HTML 报告，请用浏览器打开 print_report.html "
            "后按 Ctrl+P 打印为 PDF（设置：A4、无边距、背景图形开启）。"
        ),
    }
