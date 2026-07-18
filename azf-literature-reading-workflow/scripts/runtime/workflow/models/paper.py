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


def _discover_overview_note(reading_path: Path) -> Path:
    if reading_path.is_dir():
        candidates = sorted(reading_path.glob("【总览】*.md"))
        if candidates:
            return candidates[0]
    return reading_path / "总览.md"


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
    state: str = "created"
    artifact_id: str | None = None

    @classmethod
    def from_root(
        cls,
        root_path: Path,
        *,
        state_path_override: Path | None = None,
        artifact_id: str | None = None,
    ) -> "PaperWorkspace":
        root = root_path.resolve()
        reading = root / "阅读工作台"
        attachments = root / "附件"
        source = attachments / "原文"
        figures = attachments / "图片"
        state = state_path_override.resolve() if state_path_override else attachments / "状态"
        return cls(
            workspace_name=root.name,
            root_path=root,
            reading_workspace_path=reading,
            attachment_path=attachments,
            source_path=source,
            figure_path=figures,
            state_path=state,
            overview_note=_discover_overview_note(reading),
            quality_path=state / "quality-report.json",
            artifact_id=artifact_id,
        )

    def reading_note_path(self, role: str, title_zh: str | None) -> Path:
        return self.reading_workspace_path / reading_note_filename(role, title_zh)

    @property
    def source_language(self) -> str:
        if self.overview_note.is_file():
            text = self.overview_note.read_text(encoding="utf-8-sig", errors="replace")
            for line in text.splitlines():
                if line.startswith("原文语言:"):
                    value = line.split(":", 1)[1].strip().strip('"').casefold()
                    return "zh" if value.startswith("zh") else "en"
        if (self.source_path / "MinerU中文全文.md").is_file():
            return "zh"
        return "en"

    @property
    def mineru_markdown_path(self) -> Path:
        filename = "MinerU中文全文.md" if self.source_language == "zh" else "MinerU英文全文.md"
        return self.source_path / filename

    @property
    def fulltext_role(self) -> str:
        return "原文" if self.source_language == "zh" else "中译"

    def overview_note_for_title(self, title_zh: str | None) -> Path:
        return self.reading_note_path("总览", title_zh)

    @property
    def legacy_overview_note(self) -> Path:
        return self.reading_workspace_path / "总览.md"

    @property
    def legacy_state_path(self) -> Path:
        return self.attachment_path / "状态"

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
