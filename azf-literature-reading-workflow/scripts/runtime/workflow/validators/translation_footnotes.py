from __future__ import annotations

import re
from pathlib import Path

from workflow.services.translation_footnotes import MANAGED_ID_PREFIX

REF_RE = re.compile(r"\[\^([^\]]+)\]")
DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.M)
IMAGE_MD_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_WIKI_RE = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _body_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for line in text.splitlines():
        if DEF_RE.match(line):
            continue
        refs.update(match.group(1) for match in REF_RE.finditer(line))
    return refs


def _definitions(text: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        match = DEF_RE.match(line)
        if match:
            current = match.group(1)
            definitions[current] = line.split(":", 1)[1].strip()
        elif current and (line.startswith(" ") or line.startswith("\t")):
            definitions[current] += "\n" + line.strip()
        else:
            current = None
    return definitions


def _formula_block_issues(text: str) -> list[str]:
    issues: list[str] = []
    in_formula = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.strip() == "$$":
            in_formula = not in_formula
            continue
        if in_formula and "[^" in line:
            issues.append(f"footnote anchor inside LaTeX formula block at line {line_number}")
    return issues


def _resolve_image(note_path: Path, target: str) -> Path:
    target = target.strip().strip("<>")
    if re.match(r"^[a-z]+://", target, re.I):
        return Path("")
    path = Path(target)
    if path.is_absolute():
        return path
    return (note_path.parent / path).resolve()


def _image_link_issues(note_path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if "\u516c\u5f0f" not in line and "formula" not in line.lower():
            continue
        links = [match.group(1) for match in IMAGE_MD_RE.finditer(line)]
        links.extend(match.group(1) for match in IMAGE_WIKI_RE.finditer(line))
        for link in links:
            resolved = _resolve_image(note_path, link)
            if str(resolved) and not resolved.exists():
                issues.append(f"formula screenshot image missing at line {line_number}: {link}")
    return issues


def validate_translation_footnotes(note_path: Path) -> list[str]:
    if not note_path.is_file():
        return [f"translation note missing: {note_path}"]
    text = note_path.read_text(encoding="utf-8-sig", errors="replace")
    issues: list[str] = []
    refs = _body_refs(text)
    definitions = _definitions(text)
    for ref in sorted(refs - set(definitions)):
        issues.append(f"footnote reference missing definition: {ref}")
    for key in sorted(set(definitions) - refs):
        issues.append(f"footnote definition is not referenced: {key}")
    issues.extend(_formula_block_issues(text))
    issues.extend(_image_link_issues(note_path, text))
    source_markers = ["原文参考文献", "\u539f\u6587\u6807\u53f7", "\u539f\u6587\u9875\u811a", "PDF", "\u901a\u8baf\u4f5c\u8005", "\u90ae\u7bb1"]
    for key, value in definitions.items():
        if key.startswith(MANAGED_ID_PREFIX) and not any(marker in value for marker in source_markers):
            issues.append(f"managed footnote does not preserve original reference marker/source wording: {key}")
    return issues
