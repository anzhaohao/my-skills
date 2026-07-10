from __future__ import annotations

from pathlib import Path


def write_support_note(path: Path, title: str, warning: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {title}\n\n> [!warning] {warning}\n", encoding="utf-8")
    return path

