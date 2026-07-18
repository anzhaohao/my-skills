from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ArtifactRun:
    """One immutable-on-history machine-output run for a paper workspace."""

    artifact_id: str
    root_path: Path
    paper_workspace: Path

    @property
    def state_path(self) -> Path:
        return self.root_path / "state"

    @property
    def parser_path(self) -> Path:
        return self.root_path / "parser"

    @property
    def logs_path(self) -> Path:
        return self.root_path / "logs"

    @property
    def manifest_path(self) -> Path:
        return self.root_path / "run-manifest.json"

    @property
    def quality_path(self) -> Path:
        return self.state_path / "quality-report.json"

    @property
    def source_anchor_path(self) -> Path:
        return self.state_path / "source-anchors.json"

    @property
    def figure_manifest_path(self) -> Path:
        return self.state_path / "figure_extraction_manifest.json"

    @property
    def translation_audit_path(self) -> Path:
        return self.state_path / "translation-audit.json"

