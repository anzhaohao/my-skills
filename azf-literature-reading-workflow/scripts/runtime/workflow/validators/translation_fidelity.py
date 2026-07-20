from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.validators.translation_footnotes import validate_translation_footnotes

REQUIRED_MODE = "faithful_sentence_by_sentence"
FORBIDDEN_PLACEHOLDER_MARKERS = [
    "节级中译阅读初版",
    "# 阅读导入",
    "# 解析来源节选",
    "# 待正式生成",
    "以下内容来自本地 MinerU 解析",
    "扩展为逐段中文全译",
]

SUSPICIOUS_TABLE_LATEX_OCR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("SPM table label misread as bold LaTeX", re.compile(r"\\mathbf\s*\{\s*S\s*P\s*M", re.I)),
    ("Yes/Υ table cell misread as symbolic LaTeX", re.compile(r"\\boldsymbol\s*\{\s*\\Upsilon", re.I)),
    ("Yes table cell misread as sans-serif LaTeX", re.compile(r"\\mathsf\s*\{\s*e\s*s", re.I)),
    ("64 x 64 table note misread as malformed LaTeX", re.compile(r"\$\.\s*6\s*4\s*\\times\s*6\s*4", re.I)),
]


def suspicious_table_latex_ocr_issues(text: str) -> list[str]:
    issues: list[str] = []
    for label, pattern in SUSPICIOUS_TABLE_LATEX_OCR_PATTERNS:
        match = pattern.search(text)
        if match:
            snippet = " ".join(match.group(0).split())[:80]
            issues.append(
                "translation contains suspicious table OCR/LaTeX artifact "
                f"({label}): {snippet}; check the PDF/table screenshot and keep ordinary table labels as plain text"
            )
    return issues


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_translation_audit(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_translation_artifact(source_path: Path, note_path: Path, audit_path: Path) -> list[str]:
    issues: list[str] = []
    if not source_path.is_file():
        return [f"source Markdown missing: {source_path}"]
    if not note_path.is_file():
        return [f"translated note missing: {note_path}"]
    if not audit_path.is_file():
        return [f"translation audit missing: {audit_path}"]

    try:
        audit = load_translation_audit(audit_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"invalid translation audit: {exc}"]

    translated = note_path.read_text(encoding="utf-8-sig", errors="replace")
    for marker in FORBIDDEN_PLACEHOLDER_MARKERS:
        if marker in translated:
            issues.append(f"translation contains placeholder marker: {marker}")
    issues.extend(suspicious_table_latex_ocr_issues(translated))

    if audit.get("mode") != REQUIRED_MODE:
        issues.append(f"translation mode must be {REQUIRED_MODE}")
    if audit.get("status") != "pass":
        issues.append("translation audit status must be pass")
    if audit.get("source_sha256") != file_sha256(source_path):
        issues.append("translation audit source_sha256 does not match MinerU英文全文.md")

    source_sentences = audit.get("source_sentence_count")
    accounted_sentences = audit.get("accounted_sentence_count")
    if not isinstance(source_sentences, int) or source_sentences <= 0:
        issues.append("source_sentence_count must be a positive integer")
    if accounted_sentences != source_sentences:
        issues.append("every source sentence must be accounted for")
    if audit.get("omitted_source_sentences") not in ([], None):
        issues.append("omitted_source_sentences must be empty")
    if audit.get("added_explanatory_passages") not in ([], None):
        issues.append("added_explanatory_passages must be empty; explanations belong in the deep-reading note")

    chinese_chars = sum("\u4e00" <= char <= "\u9fff" for char in translated)
    if chinese_chars < 200:
        issues.append("translated note is too short to be a paper-level Chinese fulltext")
    issues.extend(validate_translation_footnotes(note_path))
    return issues


def _frontmatter_value(note_path: Path, key: str) -> str:
    if not note_path.is_file():
        return ""
    raw = note_path.read_text(encoding="utf-8-sig", errors="replace")
    text = raw.lstrip("\ufeff")
    frontmatter = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def validate_workspace_translation(workspace: Path, audit_path: Path | None = None) -> list[str]:
    paper = PaperWorkspace.from_root(workspace)
    source_language = _frontmatter_value(paper.overview_note, "原文语言") or "en"
    if source_language == "zh":
        source = workspace / "附件" / "原文" / "MinerU中文全文.md"
        notes = sorted((workspace / "阅读工作台").glob("【原文】*.md"))
        issues: list[str] = []
        if not source.is_file():
            issues.append(f"Chinese MinerU source missing: {source}")
        if not notes:
            issues.append(f"Chinese original note missing: {workspace}")
        if len(notes) > 1:
            issues.append(f"multiple Chinese original notes require review: {workspace}")
        return issues
    source = workspace / "附件" / "原文" / "MinerU英文全文.md"
    notes = sorted((workspace / "阅读工作台").glob("【中译】*.md"))
    if not notes:
        return [f"Chinese translation note missing: {workspace}"]
    if len(notes) > 1:
        return [f"multiple Chinese translation notes require review: {workspace}"]
    return validate_translation_artifact(source, notes[0], audit_path or paper.translation_audit_path)
