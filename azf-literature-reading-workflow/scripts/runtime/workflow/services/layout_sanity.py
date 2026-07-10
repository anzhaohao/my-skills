from __future__ import annotations

from pathlib import Path

from workflow.validators.layout_sanity import simple_layout_sanity


def review_layout(markdown_path: Path) -> dict:
    status, notes = simple_layout_sanity(markdown_path)
    return {"status": status, "notes": notes, "reviewed_pages": "preview-derived"}

