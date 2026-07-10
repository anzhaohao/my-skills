from __future__ import annotations

from pathlib import Path

from workflow.services.generated_boundaries import replace_generated_block


def write_generated_note(path: Path, generated: str, manual_suffix: str = "", force: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        merged = replace_generated_block(path.read_text(encoding="utf-8"), generated)
        path.write_text(merged, encoding="utf-8")
        return False
    path.write_text(generated.rstrip() + "\n" + manual_suffix, encoding="utf-8")
    return True


def write_if_missing(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True

