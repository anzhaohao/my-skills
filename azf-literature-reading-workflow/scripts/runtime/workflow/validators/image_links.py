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


def _find_vault_root(note_path: Path) -> Path | None:
    for candidate in [note_path.parent, *note_path.parents]:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def _short_wikilink_matches(vault_root: Path, target: str) -> list[Path]:
    clean = target.split("#", 1)[0].strip()
    if "/" in clean or "\\" in clean:
        return []
    return [candidate for candidate in vault_root.rglob(clean) if candidate.is_file()]


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
    vault_root = vault_root or _find_vault_root(note_path)
    if vault_root:
        for target in WIKILINK_IMAGE_RE.findall(text):
            if "/" in target or "\\" in target:
                issues.append(f"path-qualified wikilink image target is forbidden: {target}")
                continue
            matches = _short_wikilink_matches(vault_root, target)
            if not matches:
                issues.append(f"missing wikilink image target: {target}")
            elif len(matches) > 1:
                issues.append(f"ambiguous short wikilink image target: {target}")
    return issues
