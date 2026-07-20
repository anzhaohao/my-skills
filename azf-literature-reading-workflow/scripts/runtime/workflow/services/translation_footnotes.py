from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from workflow.models.paper import PaperWorkspace

# Legacy visible markers from an earlier implementation. New notes must not
# emit them, but the optimizer still recognizes them so one more run can clean
# old generated blocks safely.
MANAGED_START = "<!-- azf-footnotes:managed-start -->"
MANAGED_END = "<!-- azf-footnotes:managed-end -->"
FOOTNOTE_HEADING = "# 参考文献"
# Legacy long-id prefix. New notes use Obsidian native numeric footnotes such
# as [^1]; keep this prefix only for cleanup/validation compatibility.
MANAGED_ID_PREFIX = "azf-ref"
LEGACY_AUTHOR_ID_PREFIX = "azf-orig-footnote"

REFERENCE_HEADING_RE = re.compile(r"^#\s*(参考文献|References|REFERENCE|REFERENCES)\s*$", re.I)
REFERENCE_ITEM_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+(.+?)\s*$")
FOOTNOTE_REFERENCE_ITEM_RE = re.compile(r"^\s*\[\^(\d+)\]:\s+(.+?)\s*$")
BRACKET_CITATION_RE = re.compile(r"\[(\d+(?:\s*[,，、]\s*\d+)*)\](?:\s*[-–—]\s*\[(\d+)\])?")
NATIVE_NUMERIC_FOOTNOTE_RE = re.compile(r"\[\^(\d+)\]")
LEGACY_FOOTNOTE_HEADING_RE = re.compile(r"^#\s*(参考文献脚注|原文脚注)\s*$")


@dataclass(slots=True)
class TranslationFootnoteCandidate:
    footnote_id: str
    anchor_line: int
    anchor_start: int
    anchor_end: int
    definition: str
    source_kind: str
    original_marker: str
    remove_lines: list[int]


@dataclass(slots=True)
class TranslationFootnoteResult:
    workspace: str
    note_path: str
    dry_run: bool
    changed: bool
    candidates: list[dict]
    removed_lines: list[int]
    audit_path: str | None
    backup_path: str | None
    issues: list[str]


def _split_frontmatter_lines(text: str) -> tuple[list[str], int]:
    lines = text.lstrip("\ufeff").splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines, index + 1
    return lines, 0


def _translation_content_start_index(lines: list[str], start: int) -> int | None:
    """Return the first translated-content heading after the front-matter block.

    The optimizer uses an exclusion model, not a strict `# 正文` model: author
    names, affiliations, correspondence notes, received dates, copyright notes,
    and DOI lines live before the first heading in generated notes and are not
    touched. Once the first real note heading appears, sections such as `# 摘要`,
    `# Abstract`, and `# 正文` are all treated as body content until references.
    """
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("#"):
            continue
        if REFERENCE_HEADING_RE.match(stripped) or LEGACY_FOOTNOTE_HEADING_RE.match(stripped):
            return None
        return index
    return None


def _reference_heading_index(lines: list[str], start: int) -> int | None:
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if REFERENCE_HEADING_RE.match(stripped) or LEGACY_FOOTNOTE_HEADING_RE.match(stripped):
            return index
    return None


def _note_slug(workspace: PaperWorkspace) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", workspace.workspace_name).strip("-").lower()
    return slug[:48] or "paper"


def _parse_reference_items(lines: list[str], start: int) -> dict[int, str]:
    heading = _reference_heading_index(lines, start)
    if heading is None:
        return {}
    references: dict[int, list[str]] = {}
    current: int | None = None
    for line in lines[heading + 1 :]:
        if line.strip() in {MANAGED_START, MANAGED_END}:
            continue
        if line.startswith("#") and not REFERENCE_ITEM_RE.match(line):
            break
        match = REFERENCE_ITEM_RE.match(line)
        if match:
            number = int(match.group(1) or match.group(2))
            current = number
            references[number] = [match.group(3).strip()]
            continue
        footnote_match = FOOTNOTE_REFERENCE_ITEM_RE.match(line)
        if footnote_match:
            number = int(footnote_match.group(1))
            current = number
            value = footnote_match.group(2).strip()
            value = re.sub(rf"^原文参考文献\s*\[{number}\][：:]\s*", "", value)
            references[number] = [value]
        elif current is not None and line.strip():
            references[current].append(line.strip())
    return {number: re.sub(r"\s+", " ", " ".join(parts)).strip() for number, parts in references.items()}


def _expand_numbers(first_group: str, range_end: str | None) -> list[int]:
    numbers = [int(item) for item in re.split(r"\s*[,，、]\s*", first_group.strip()) if item]
    if range_end and numbers:
        start = numbers[-1]
        end = int(range_end)
        if end >= start:
            numbers = numbers[:-1] + list(range(start, end + 1))
        else:
            numbers.append(end)
    deduped: list[int] = []
    for number in numbers:
        if number not in deduped:
            deduped.append(number)
    return deduped


def _line_spans_formula_boundary(line: str) -> bool:
    return line.strip() == "$$"


def _is_non_body_caption_or_asset_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("!"):
        return True
    # This command handles body reference markers only. Keep figure/table
    # captions unchanged unless a later reviewed caption rule is added.
    if re.match(r"^(图|表)\s*\d+(?:[.．、:：]|\s)", stripped):
        return True
    if re.match(r"^(Fig\.|Figure|Table)\s*\d+", stripped, re.I):
        return True
    return False


def _citation_occurrences(lines: list[str], body_start: int, reference_start: int | None) -> list[tuple[int, int, int, str, list[int]]]:
    stop = reference_start if reference_start is not None else len(lines)
    content_start = _translation_content_start_index(lines, body_start)
    if content_start is None:
        return []
    occurrences: list[tuple[int, int, int, str, list[int]]] = []
    in_formula = False
    # Process translated content by exclusion: skip front matter before the
    # first heading, stop before references, and ignore formula/caption/assets.
    # Abstract sections are body content and are included by default.
    for index in range(content_start, stop):
        line = lines[index]
        if _line_spans_formula_boundary(line):
            in_formula = not in_formula
            continue
        if in_formula or _is_non_body_caption_or_asset_line(line):
            continue
        matches: list[tuple[int, int, str, list[int]]] = []
        for match in BRACKET_CITATION_RE.finditer(line):
            marker = match.group(0)
            numbers = _expand_numbers(match.group(1), match.group(2))
            if numbers:
                matches.append((match.start(), match.end(), marker, numbers))
        for match in NATIVE_NUMERIC_FOOTNOTE_RE.finditer(line):
            marker = match.group(0)
            matches.append((match.start(), match.end(), marker, [int(match.group(1))]))
        for start, end, marker, numbers in sorted(matches):
            occurrences.append((index, start, end, marker, numbers))
    return occurrences


def collect_translation_footnote_candidates(workspace: PaperWorkspace, text: str) -> list[TranslationFootnoteCandidate]:
    lines, body_start = _split_frontmatter_lines(text)
    reference_start = _reference_heading_index(lines, body_start)
    references = _parse_reference_items(lines, body_start)
    if not references:
        return []
    candidates: list[TranslationFootnoteCandidate] = []
    slug = _note_slug(workspace)
    for line_index, start, end, marker, numbers in _citation_occurrences(lines, body_start, reference_start):
        for number in numbers:
            reference = references.get(number)
            if not reference:
                continue
            candidates.append(
                TranslationFootnoteCandidate(
                    footnote_id=str(number),
                    anchor_line=line_index,
                    anchor_start=start,
                    anchor_end=end,
                    definition=f"原文参考文献 [{number}]：{reference}",
                    source_kind="body_reference_citation",
                    original_marker=marker,
                    remove_lines=[],
                )
            )
    return candidates


def _remove_managed_anchors(text: str) -> str:
    prefixes = [re.escape(MANAGED_ID_PREFIX), re.escape(LEGACY_AUTHOR_ID_PREFIX)]
    return re.sub(r"\[\^(?:" + "|".join(prefixes) + r")-[^\]]+\]", "", text)


def _strip_managed_block(text: str) -> str:
    if MANAGED_START not in text or MANAGED_END not in text:
        return text
    pattern = re.compile(r"\n?" + re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END) + r"\n?", re.S)
    text = pattern.sub("\n", text)
    for heading in [FOOTNOTE_HEADING, "# 参考文献脚注", "# 原文脚注"]:
        empty_heading = re.compile(r"\n" + re.escape(heading) + r"\n\s*(?=\n# |\Z)", re.S)
        text = empty_heading.sub("\n", text)
    return text


def _drop_reference_sections(lines: list[str], body_start: int) -> list[str]:
    """Remove existing reference-like sections before appending managed definitions.

    The command intentionally lets managed Obsidian footnotes replace the old
    bibliography list, so the note ends with one `# 参考文献` section rather than
    both `# 参考文献` and `# 参考文献脚注`.
    """
    result: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if index >= body_start and (REFERENCE_HEADING_RE.match(line.strip()) or LEGACY_FOOTNOTE_HEADING_RE.match(line.strip())):
            index += 1
            while index < len(lines) and not lines[index].startswith("#"):
                index += 1
            continue
        result.append(line)
        index += 1
    return result


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    blank_count = 0
    for line in lines:
        if line.strip():
            blank_count = 0
            collapsed.append(line)
        else:
            blank_count += 1
            if blank_count <= 2:
                collapsed.append("")
    return collapsed


def _anchor_suffix(candidates: list[TranslationFootnoteCandidate]) -> str:
    ordered: list[str] = []
    for candidate in candidates:
        anchor = f"[^{candidate.footnote_id}]"
        if anchor not in ordered:
            ordered.append(anchor)
    return "".join(ordered)


def _native_numeric_footnote_suffix(candidates: list[TranslationFootnoteCandidate]) -> str:
    numbers: list[int] = []
    for candidate in candidates:
        number_match = re.search(r"^(?:.*-)?(\d+)$", candidate.footnote_id)
        if not number_match:
            continue
        number = int(number_match.group(1))
        if number not in numbers:
            numbers.append(number)
    return "".join(f"[^{number}]" for number in numbers)


def _apply_candidates(text: str, candidates: list[TranslationFootnoteCandidate]) -> tuple[str, list[int]]:
    text = _strip_managed_block(_remove_managed_anchors(text))
    lines, body_start = _split_frontmatter_lines(text)
    by_occurrence: dict[tuple[int, int, int, str], list[TranslationFootnoteCandidate]] = {}
    for candidate in candidates:
        by_occurrence.setdefault(
            (candidate.anchor_line, candidate.anchor_start, candidate.anchor_end, candidate.original_marker),
            [],
        ).append(candidate)
    for (line_index, start, end, marker), marker_candidates in sorted(by_occurrence.items(), reverse=True):
        if not (0 <= line_index < len(lines)):
            continue
        suffix = _native_numeric_footnote_suffix(marker_candidates)
        if not suffix:
            suffix = _anchor_suffix(marker_candidates)
        line = lines[line_index]
        if start < 0 or end > len(line) or line[start:end] != marker:
            fallback = line.find(marker)
            if fallback < 0:
                lines[line_index] = line.rstrip() + suffix
                continue
            start = fallback
            end = fallback + len(marker)
        if line[end : end + len(suffix)] == suffix:
            continue
        lines[line_index] = line[:start] + suffix + line[end:]
    lines = _drop_reference_sections(lines, body_start)
    kept = _collapse_blank_lines(lines)
    body = "\n".join(kept).rstrip()
    unique_definitions: dict[str, str] = {}
    for item in candidates:
        unique_definitions.setdefault(item.footnote_id, item.definition)
    if unique_definitions:
        def _definition_sort_key(item: tuple[str, str]) -> tuple[int, str]:
            match = re.search(r"^(?:.*-)?(\d+)$", item[0])
            if match:
                return (int(match.group(1)), item[0])
            return (10**9, item[0])

        definition_lines: list[str] = []
        for key, value in sorted(unique_definitions.items(), key=_definition_sort_key):
            match = re.search(r"^(?:.*-)?(\d+)$", key)
            definition_key = match.group(1) if match else key
            definition_lines.append(f"[^{definition_key}]: {value}")
        definitions = "\n".join(definition_lines)
        body += f"\n\n{FOOTNOTE_HEADING}\n\n{definitions}\n"
    else:
        body += "\n"
    return body, []


def _default_backup_root() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("E:/software/CodexPlusPlus/Codex备份") / f"{stamp}_中译正文参考文献脚注_apply前备份"


def optimize_translation_footnotes(
    workspace_root: Path,
    *,
    apply: bool = False,
    backup_root: Path | None = None,
) -> TranslationFootnoteResult:
    workspace = PaperWorkspace.from_root(workspace_root)
    notes = sorted(workspace.reading_workspace_path.glob("【中译】*.md"))
    if not notes:
        return TranslationFootnoteResult(str(workspace.root_path), "", not apply, False, [], [], None, None, ["Chinese translation note missing"])
    if len(notes) > 1:
        return TranslationFootnoteResult(str(workspace.root_path), "", not apply, False, [], [], None, None, ["multiple Chinese translation notes require review"])
    note = notes[0]
    original = note.read_text(encoding="utf-8-sig", errors="replace")
    candidates = collect_translation_footnote_candidates(workspace, original)
    if candidates:
        optimized, removed = _apply_candidates(original, candidates)
    else:
        optimized, removed = original, []
    changed = optimized != original
    backup_path: Path | None = None
    audit_path = workspace.state_path / "translation-footnotes-audit.json"
    issues: list[str] = []
    if apply and changed:
        root = backup_root or _default_backup_root()
        backup_path = root / workspace.workspace_name / note.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(note, backup_path)
        note.write_text(optimized, encoding="utf-8")
    if apply:
        workspace.state_path.mkdir(parents=True, exist_ok=True)
        audit = {
            "status": "pass",
            "mode": "body_reference_citation_footnotes",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "note_path": str(note),
            "candidate_count": len(candidates),
            "changed": changed,
            "candidates": [asdict(item) for item in candidates],
            "removed_source_note_lines_1based": [index + 1 for index in removed],
            "scope": "Exclusion model: convert bibliography citations such as [1], [2,3], and [1]-[3] in translated content, including abstracts by default. Author/affiliation/correspondence/front-matter metadata, bibliography definitions, generated footnote definitions, PDF footers, and author-line superscripts must remain in place.",
            "format": "Use Obsidian native numeric footnotes. Definitions replace the bibliography body under # 参考文献, with no visible managed comments and no separate # 参考文献脚注 section.",
            "formula_policy": "Never insert Obsidian footnote anchors inside LaTeX formula blocks. If a citation marker is attached to a formula, keep the formula intact and handle it outside the formula block after PDF/MinerU review.",
        }
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return TranslationFootnoteResult(
        workspace=str(workspace.root_path),
        note_path=str(note),
        dry_run=not apply,
        changed=changed,
        candidates=[asdict(item) for item in candidates],
        removed_lines=[index + 1 for index in removed],
        audit_path=str(audit_path) if apply else None,
        backup_path=str(backup_path) if backup_path else None,
        issues=issues,
    )
