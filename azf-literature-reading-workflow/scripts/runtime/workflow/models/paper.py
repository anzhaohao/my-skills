from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PaperSource:
    zotero_key: str | None = None
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
    source_path: Path
    figure_path: Path
    overview_note: Path
    quality_path: Path
    state: str = "created"

    @classmethod
    def from_root(cls, root_path: Path) -> "PaperWorkspace":
        root = root_path.resolve()
        reading = root / "阅读工作台"
        source = root / "附件" / "原文"
        figures = root / "附件" / "图片"
        return cls(
            workspace_name=root.name,
            root_path=root,
            reading_workspace_path=reading,
            source_path=source,
            figure_path=figures,
            overview_note=reading / "总览.md",
            quality_path=root / "quality-report.json",
        )


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

