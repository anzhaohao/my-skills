from __future__ import annotations

from pathlib import Path


def simple_layout_sanity(markdown_path: Path) -> tuple[str, list[str]]:
    if not markdown_path.exists():
        return "fail", [f"missing MinerU markdown: {markdown_path}"]
    text = markdown_path.read_text(encoding="utf-8", errors="replace")
    notes: list[str] = []
    if len(text.strip()) < 500:
        notes.append("parsed text is very short; manual layout review required")
        return "suspect", notes
    if text.count("\n") < 20:
        notes.append("parsed text has too few line breaks; section order may be collapsed")
        return "suspect", notes
    if "references" not in text.lower() and "参考文献" not in text:
        notes.append("references section not detected; verify parse completeness")
    return "pass" if not notes else "suspect", notes
