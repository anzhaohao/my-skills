from __future__ import annotations

import shutil
from pathlib import Path


def find_mineru_auto_dir(output_root: Path) -> Path | None:
    """Find the MinerU output folder that contains the accepted Markdown/JSON set."""
    if not output_root.exists():
        return None
    candidates = [output_root, *output_root.rglob("auto")]
    for candidate in candidates:
        has_markdown = any(candidate.glob("*.md"))
        has_middle = any(candidate.glob("*_middle.json"))
        if has_markdown and has_middle:
            return candidate
    return None


def _first(source_dir: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(source_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def attach_mineru_outputs(output_root: Path, source_dir: Path, *, source_language: str = "en") -> dict[str, str | None]:
    """Expose accepted MinerU Markdown in the vault while keeping raw output and images in cache."""
    auto_dir = find_mineru_auto_dir(output_root)
    result: dict[str, str | None] = {
        "auto_dir": str(auto_dir) if auto_dir else None,
        "markdown": None,
        "raw_output": None,
        "content_list": None,
        "content_list_v2": None,
        "images_dir": None,
    }
    if not auto_dir:
        return result

    source_dir.mkdir(parents=True, exist_ok=True)
    source_markdown = _first(auto_dir, ["*.md"])
    filename = "MinerU中文全文.md" if source_language == "zh" else "MinerU英文全文.md"
    markdown = source_dir / filename if source_markdown else None
    if source_markdown and markdown:
        shutil.copy2(source_markdown, markdown)

    raw = _first(auto_dir, ["*_middle.json", "*middle*.json"])
    content = _first(auto_dir, ["*_content_list.json"])
    content_v2 = _first(auto_dir, ["*_content_list_v2.json"])
    images = auto_dir / "images"

    result.update(
        {
            "markdown": str(markdown) if markdown else None,
            "raw_output": str(raw) if raw else None,
            "content_list": str(content) if content else None,
            "content_list_v2": str(content_v2) if content_v2 else None,
            "images_dir": str(images) if images.is_dir() else None,
        }
    )
    return result
