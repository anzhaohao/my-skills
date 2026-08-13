from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def safe_note_title(title: str | None, *, fallback: str = "未命名论文", max_length: int = 90) -> str:
    value = (title or "").strip() or fallback
    value = re.sub(r"\s+", " ", value)
    value = "".join("－" if char in INVALID_FILENAME_CHARS else char for char in value)
    value = value.strip(" .") or fallback
    return value[:max_length].rstrip(" .") or fallback


def reading_note_filename(role: str, title_zh: str | None) -> str:
    return f"【{role}】{safe_note_title(title_zh)}.md"


def source_pdf_filename(title_zh: str | None) -> str:
    return f"【原文】{safe_note_title(title_zh)}.pdf"


def mineru_source_filename(title_zh: str | None) -> str:
    return f"【MinerU原文】{safe_note_title(title_zh)}.md"


def _discover_overview_note(reading_path: Path) -> Path:
    if reading_path.is_dir():
        candidates = sorted(reading_path.glob("【总览】*.md"))
        if candidates:
            return candidates[0]
    return reading_path / "总览.md"


def _frontmatter_value(note: Path, key: str) -> str:
    if not note.is_file():
        return ""
    text = note.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---") or text.count("---") < 2:
        return ""
    frontmatter = text.split("---", 2)[1]
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _discover_asset(directory: Path, pattern: str, legacy_names: tuple[str, ...]) -> Path | None:
    if directory.is_dir():
        candidates = sorted(directory.glob(pattern))
        if len(candidates) == 1:
            return candidates[0]
        for name in legacy_names:
            legacy = directory / name
            if legacy.is_file():
                return legacy
    return None


@dataclass(slots=True)
class PaperSource:
    zotero_key: str | None = None
    zotero_pdf_attachment_key: str | None = None
    citekey: str | None = None
    title_en: str = ""
    title_zh: str | None = None
    authors: list[str] = field(default_factory=list)
    year: str | None = None
    venue: str | None = None
    doi: str | None = None
    collections: list[str] = field(default_factory=list)
    pdf_attachments: list[Path] = field(default_factory=list)
    zotero_link: str | None = None
    source_language: str = "en"


@dataclass(slots=True)
class TopicFolder:
    topic_name: str
    root_path: Path
    concept_classroom_path: Path
    paper_workspaces: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class PaperWorkspace:
    workspace_name: str
    root_path: Path
    reading_workspace_path: Path
    attachment_path: Path
    source_path: Path
    figure_path: Path
    state_path: Path
    overview_note: Path
    quality_path: Path
    title_zh: str = ""
    source_language: str = "en"
    artifact_root: Path | None = None
    artifact_id: str | None = None
    state: str = "created"

    @classmethod
    def from_root(
        cls,
        root_path: Path,
        *,
        state_path: Path | None = None,
        artifact_root: Path | None = None,
        artifact_id: str | None = None,
    ) -> "PaperWorkspace":
        root = root_path.resolve()
        reading = root / "阅读工作台"
        attachments = root / "附件"
        source = attachments / "原文"
        figures = attachments / "图片"
        overview = _discover_overview_note(reading)
        title_zh = _frontmatter_value(overview, "中文短标题") or _frontmatter_value(overview, "中文题名")
        if not title_zh and overview.name.startswith("【总览】"):
            title_zh = overview.stem.removeprefix("【总览】")
        source_language = _frontmatter_value(overview, "原文语言") or "en"
        resolved_state = state_path.resolve() if state_path else attachments / "状态"
        return cls(
            workspace_name=root.name,
            root_path=root,
            reading_workspace_path=reading,
            attachment_path=attachments,
            source_path=source,
            figure_path=figures,
            state_path=resolved_state,
            overview_note=overview,
            quality_path=resolved_state / "quality-report.json",
            title_zh=title_zh,
            source_language=source_language,
            artifact_root=artifact_root.resolve() if artifact_root else None,
            artifact_id=artifact_id,
        )

    def reading_note_path(self, role: str, title_zh: str | None) -> Path:
        return self.reading_workspace_path / reading_note_filename(role, title_zh)

    def overview_note_for_title(self, title_zh: str | None) -> Path:
        return self.reading_note_path("总览", title_zh)

    def source_pdf_path(self, title_zh: str | None = None) -> Path:
        if title_zh:
            return self.source_path / source_pdf_filename(title_zh)
        discovered = _discover_asset(self.source_path, "【原文】*.pdf", ("原文.pdf",))
        return discovered or self.source_path / source_pdf_filename(self.title_zh)

    def mineru_source_path(self, title_zh: str | None = None) -> Path:
        if title_zh:
            return self.source_path / mineru_source_filename(title_zh)
        discovered = _discover_asset(
            self.source_path,
            "【MinerU原文】*.md",
            ("MinerU英文全文.md", "MinerU中文全文.md"),
        )
        return discovered or self.source_path / mineru_source_filename(self.title_zh)

    def chinese_fulltext_path(self, title_zh: str | None = None) -> Path:
        return self.reading_note_path("中译", title_zh or self.title_zh)

    @property
    def legacy_overview_note(self) -> Path:
        return self.reading_workspace_path / "总览.md"

    @property
    def source_anchor_path(self) -> Path:
        return self.state_path / "source-anchors.json"

    @property
    def figure_manifest_path(self) -> Path:
        return self.state_path / "figure_extraction_manifest.json"

    @property
    def translation_audit_path(self) -> Path:
        return self.state_path / "translation-audit.json"

    @property
    def metadata_verification_path(self) -> Path:
        return self.state_path / "metadata-verification.json"

    @property
    def mineru_reuse_audit_path(self) -> Path:
        return self.state_path / "mineru-reuse-audit.json"

    @property
    def source_review_status_path(self) -> Path:
        return self.state_path / "source-review-status.json"

    @property
    def translation_footnotes_audit_path(self) -> Path:
        return self.state_path / "translation-footnotes-audit.json"


@dataclass(slots=True)
class ParsedSource:
    mineru_markdown: Path
    mineru_raw_output: Path
    mineru_images: list[Path] = field(default_factory=list)
    parse_method: str = "pending"
    parse_status: str = "pending"
    source_spans: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReadingArtifact:
    artifact_type: str
    path: Path
    generated: bool = True
    source_anchor_ids: list[str] = field(default_factory=list)
