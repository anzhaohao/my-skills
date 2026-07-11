from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace


def locate_source_assets(workspace_root: Path) -> dict[str, Path | None]:
    workspace = PaperWorkspace.from_root(workspace_root)
    return {
        "pdf": workspace.source_path / "原文.pdf" if (workspace.source_path / "原文.pdf").exists() else None,
        "mineru_markdown": workspace.source_path / "MinerU英文全文.md" if (workspace.source_path / "MinerU英文全文.md").exists() else None,
        "mineru_raw": workspace.source_path / "MinerU原始输出.json" if (workspace.source_path / "MinerU原始输出.json").exists() else None,
        "figure_manifest": workspace.figure_manifest_path if workspace.figure_manifest_path.exists() else None,
        "source_anchors": workspace.source_anchor_path if workspace.source_anchor_path.exists() else None,
    }

