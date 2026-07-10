from __future__ import annotations

import shutil
from pathlib import Path


def ensure_source_pdf(pdf_path: Path, source_dir: Path, copy_name: str = "原文.pdf") -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)
    target = source_dir / copy_name
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if target.exists() and target.resolve() == pdf_path.resolve():
        return target
    if not target.exists():
        shutil.copy2(pdf_path, target)
    return target


def classify_pdf_attachments(paths: list[Path]) -> dict[str, list[str]]:
    existing = [str(path) for path in paths if path.exists()]
    missing = [str(path) for path in paths if not path.exists()]
    primary = existing[:1]
    supplementary = existing[1:]
    return {"primary": primary, "supplementary": supplementary, "missing": missing}

