from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_workspace_contract_detects_required_files(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    workspace.source_path.mkdir(parents=True)
    workspace.figure_path.mkdir(parents=True)
    workspace.overview_note.write_text("---\n类型: 论文总览\n---\n\n## 导航\n\n## 待办与备注\n", encoding="utf-8")
    (workspace.source_path / "原文.pdf").write_bytes(b"%PDF-1.4\n")

    assert validate_workspace_contract(workspace.root_path) == []