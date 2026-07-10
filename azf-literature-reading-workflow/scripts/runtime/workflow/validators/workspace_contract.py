from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace


def validate_workspace_contract(workspace_root: Path) -> list[str]:
    workspace = PaperWorkspace.from_root(workspace_root)
    issues: list[str] = []
    required_dirs = [
        workspace.reading_workspace_path,
        workspace.source_path,
        workspace.figure_path,
    ]
    required_files = [
        workspace.overview_note,
        workspace.source_path / "原文.pdf",
    ]
    for folder in required_dirs:
        if not folder.is_dir():
            issues.append(f"missing folder: {folder}")
    for file_path in required_files:
        if not file_path.is_file():
            issues.append(f"missing file: {file_path}")
    if workspace.overview_note.exists():
        text = workspace.overview_note.read_text(encoding="utf-8", errors="replace")
        if "类型: 论文总览" not in text and "type: paper-overview" not in text:
            issues.append("overview missing paper-overview type marker")
        for marker in ["## 导航", "## 待办与备注"]:
            if marker not in text:
                issues.append(f"overview missing marker: {marker}")
    return issues


def workspace_status(workspace_root: Path) -> str:
    return "pass" if not validate_workspace_contract(workspace_root) else "fail"