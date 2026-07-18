from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource
from workflow.services.workspace_naming import infer_title_from_pdf, infer_year_from_name


def paper_source_from_pdf(
    pdf_path: Path,
    title_zh: str | None = None,
    *,
    title_en: str | None = None,
    authors: list[str] | None = None,
    year: str | None = None,
    venue: str | None = None,
    doi: str | None = None,
    citekey: str | None = None,
    zotero_key: str | None = None,
    zotero_pdf_attachment_key: str | None = None,
    source_language: str = "en",
) -> PaperSource:
    return PaperSource(
        zotero_key=zotero_key,
        zotero_pdf_attachment_key=zotero_pdf_attachment_key,
        citekey=citekey,
        title_en=title_en or infer_title_from_pdf(pdf_path),
        title_zh=title_zh,
        authors=authors or [],
        year=year or infer_year_from_name(pdf_path.name),
        venue=venue,
        doi=doi,
        pdf_attachments=[pdf_path],
        source_language=source_language,
    )


def zotero_boundary_status() -> dict:
    return {
        "available": False,
        "status": "not_connected",
        "note": "Zotero/obsidian-vault-mcp adapter boundary is defined; direct MCP calls are not invoked by this local CLI.",
    }
