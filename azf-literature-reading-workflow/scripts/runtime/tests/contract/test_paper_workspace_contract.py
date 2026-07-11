from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_workspace_contract_detects_required_files(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    workspace.source_path.mkdir(parents=True)
    workspace.figure_path.mkdir(parents=True)
    workspace.state_path.mkdir(parents=True)
    workspace.overview_note.write_text(
        """---
\u7c7b\u578b: \u8bba\u6587\u603b\u89c8
\u539f\u6587PDF: "[[\u9644\u4ef6/\u539f\u6587/\u539f\u6587.pdf|\u539f\u6587.pdf]]"
MinerU\u82f1\u6587\u5168\u6587: "[[\u9644\u4ef6/\u539f\u6587/MinerU\u82f1\u6587\u5168\u6587.md|MinerU\u82f1\u6587\u5168\u6587.md]]"
---

## \u5bfc\u822a

## \u4e0b\u4e00\u6b65
""",
        encoding="utf-8",
    )
    (workspace.source_path / "\u539f\u6587.pdf").write_bytes(b"%PDF-1.4\n")

    assert validate_workspace_contract(workspace.root_path) == []
