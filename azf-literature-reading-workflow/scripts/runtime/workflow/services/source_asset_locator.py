from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace


def locate_source_assets(workspace_root: Path, artifact_root: Path | None = None) -> dict[str, Path | None]:
    from workflow.services.artifact_runs import workspace_with_artifacts

    workspace = workspace_with_artifacts(workspace_root, artifact_root)
    pdf = workspace.source_pdf_path()
    mineru = workspace.chinese_fulltext_path() if workspace.source_language == "zh" else workspace.mineru_source_path()
    return {
        "pdf": pdf if pdf.exists() else None,
        "mineru_markdown": mineru if mineru.exists() else None,
        "mineru_raw": workspace.source_path / "MinerU原始输出.json" if (workspace.source_path / "MinerU原始输出.json").exists() else None,
        "figure_manifest": workspace.figure_manifest_path if workspace.figure_manifest_path.exists() else None,
        "source_anchors": workspace.source_anchor_path if workspace.source_anchor_path.exists() else None,
    }

