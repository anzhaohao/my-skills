from __future__ import annotations

import json
from pathlib import Path


def normalize_mineru_output(markdown_path: Path, raw_output_path: Path) -> dict:
    markdown = markdown_path.read_text(encoding="utf-8", errors="replace") if markdown_path.exists() else ""
    raw = json.loads(raw_output_path.read_text(encoding="utf-8")) if raw_output_path.exists() else {}
    pages = raw.get("pages", [])
    return {
        "markdown_path": str(markdown_path),
        "raw_output_path": str(raw_output_path),
        "char_count": len(markdown),
        "page_count": len(pages),
        "accepted_as_mineru": raw.get("accepted_as_mineru", True),
    }

