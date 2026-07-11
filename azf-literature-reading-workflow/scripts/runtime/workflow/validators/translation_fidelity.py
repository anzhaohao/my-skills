from __future__ import annotations

import hashlib
import json
from pathlib import Path

from workflow.models.paper import PaperWorkspace

REQUIRED_MODE = "faithful_sentence_by_sentence"
FORBIDDEN_PLACEHOLDER_MARKERS = [
    "节级中译阅读初版",
    "# 阅读导入",
    "# 解析来源节选",
    "# 待正式生成",
    "以下内容来自本地 MinerU 解析",
    "扩展为逐段中文全译",
]


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
    return issues


def validate_workspace_translation(workspace: Path) -> list[str]:
    source = workspace / "附件" / "原文" / "MinerU英文全文.md"
    notes = sorted((workspace / "阅读工作台").glob("【中译】*.md"))
    if not notes:
        return [f"Chinese translation note missing: {workspace}"]
    if len(notes) > 1:
        return [f"multiple Chinese translation notes require review: {workspace}"]
    return validate_translation_artifact(source, notes[0], PaperWorkspace.from_root(workspace).translation_audit_path)
