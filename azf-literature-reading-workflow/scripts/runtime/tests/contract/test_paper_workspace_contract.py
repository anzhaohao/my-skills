from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_workspace_contract_detects_required_files(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    workspace.source_path.mkdir(parents=True)
    workspace.figure_path.mkdir(parents=True)
    workspace.state_path.mkdir(parents=True)
    overview = workspace.reading_note_path("总览", "测试论文")
    workspace.overview_note = overview
    overview.write_text(
        """---
笔记类型: 索引
笔记状态: 待整理
论文笔记类型: 论文总览
中文题名: "测试论文"
Zotero条目键: "ABCD1234"
Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"
原文PDF: "[[附件/原文/原文.pdf|原文.pdf]]"
MinerU英文全文: "[[附件/原文/MinerU英文全文.md|MinerU英文全文.md]]"
---

# 导航

# 下一步
""",
        encoding="utf-8",
    )
    for role in ["中译", "精读", "图表", "问答"]:
        workspace.reading_note_path(role, "测试论文").write_text(
            f"""---
笔记类型: 知识
笔记状态: 待整理
论文笔记类型: {role}
Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"
---

# 内容
""",
            encoding="utf-8",
        )
    (workspace.source_path / "原文.pdf").write_bytes(b"%PDF-1.4\n")

    assert validate_workspace_contract(workspace.root_path) == []
