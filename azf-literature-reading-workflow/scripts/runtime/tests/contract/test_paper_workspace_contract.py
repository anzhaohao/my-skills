from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_workspace_contract_detects_required_files(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    workspace.source_path.mkdir(parents=True)
    overview = workspace.reading_note_path("总览", "测试论文")
    workspace.overview_note = overview
    overview.write_text(
        """---
笔记类型: 索引
笔记状态: 待整理
论文笔记类型: 论文总览
中文题名: "测试论文"
中文短标题: "测试论文"
原文语言: en
Zotero条目键: "ABCD1234"
Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"
中文全文: "[[【中译】测试论文.md|中译笔记]]"
原文PDF: "[[【原文】测试论文.pdf|原文PDF]]"
MinerU原文: "[[【MinerU原文】测试论文.md|MinerU原文]]"
---

# 导航

# 下一步
""",
        encoding="utf-8",
    )
    workspace.reading_note_path("中译", "测试论文").write_text(
        """---
笔记类型: 知识
笔记状态: 待整理
论文笔记类型: 中文全文
Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"
---

# 内容
""",
        encoding="utf-8",
    )
    workspace.source_pdf_path("测试论文").write_bytes(b"%PDF-1.4\n")
    workspace.mineru_source_path("测试论文").write_text("Source sentence.", encoding="utf-8")

    assert validate_workspace_contract(workspace.root_path) == []


def test_optional_notes_are_allowed_when_explicitly_generated(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    for role in ["精读", "图表", "问答"]:
        workspace.reading_note_path(role, "测试论文").write_text("explicit", encoding="utf-8")

    issues = validate_workspace_contract(workspace.root_path)

    assert not any("default reading workspace still contains" in issue for issue in issues)


def test_workspace_contract_rejects_path_qualified_wikilinks(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    (workspace.reading_workspace_path / "人工.md").write_text(
        "![[../附件/图片/Fig-01.png]]\n",
        encoding="utf-8",
    )

    issues = validate_workspace_contract(workspace.root_path)

    assert any("path-qualified Wikilink target" in issue for issue in issues)


def test_workspace_contract_rejects_ambiguous_short_wikilinks(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    workspace = PaperWorkspace.from_root(vault / "papers" / "Paper")
    workspace.reading_workspace_path.mkdir(parents=True)
    (workspace.reading_workspace_path / "人工.md").write_text("![[Fig-01.png]]\n", encoding="utf-8")
    for folder in [vault / "assets-a", vault / "assets-b"]:
        folder.mkdir()
        (folder / "Fig-01.png").write_bytes(b"png")

    issues = validate_workspace_contract(workspace.root_path)

    assert any("ambiguous short Wikilink target" in issue for issue in issues)
