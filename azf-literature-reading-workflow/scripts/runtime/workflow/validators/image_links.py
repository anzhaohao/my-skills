from __future__ import annotations

import re
from pathlib import Path

MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
WIKILINK_IMAGE_RE = re.compile(r"!\[\[([^|\]]+)(?:\|[^\]]*)?\]\]")


def _resolve_markdown_target(note_path: Path, target: str) -> Path:
    clean = target.split("#", 1)[0].strip()
    if clean.startswith(("http://", "https://")):
        return Path(clean)
    return (note_path.parent / clean).resolve()


def _resolve_wikilink_target(vault_root: Path, target: str) -> Path:
    clean = target.split("#", 1)[0].strip()
    return (vault_root / clean).resolve()


def extract_image_links(markdown: str) -> list[str]:
    links = MARKDOWN_IMAGE_RE.findall(markdown)
    links.extend(WIKILINK_IMAGE_RE.findall(markdown))
    return links


def validate_image_links(note_path: Path, vault_root: Path | None = None) -> list[str]:
    if not note_path.exists():
        return [f"missing note: {note_path}"]
    text = note_path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    for target in MARKDOWN_IMAGE_RE.findall(text):
        if target.startswith(("http://", "https://")):
            issues.append(f"remote image link is not local: {target}")
            continue
        resolved = _resolve_markdown_target(note_path, target)
        if not resolved.exists():
            issues.append(f"missing markdown image target: {target}")
    if vault_root:
        for target in WIKILINK_IMAGE_RE.findall(text):
            resolved = _resolve_wikilink_target(vault_root, target)
            if not resolved.exists():
                issues.append(f"missing wikilink image target: {target}")
    return issues

