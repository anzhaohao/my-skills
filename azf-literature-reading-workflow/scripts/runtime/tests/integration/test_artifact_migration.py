import json
from argparse import Namespace
from pathlib import Path

from workflow.commands.migrate_artifacts import run


def _make_legacy_chinese_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "vault" / "paper-root" / "Paper"
    reading = workspace / "阅读工作台"
    source = workspace / "附件" / "原文"
    state = workspace / "附件" / "状态"
    figures = workspace / "附件" / "图片"
    for folder in [reading, source, state, figures]:
        folder.mkdir(parents=True)
    overview = reading / "【总览】测试中文论文.md"
    overview.write_text(
        """---
笔记类型: 索引
笔记状态: 可用
论文笔记类型: 论文总览
中文题名: "测试中文论文"
DOI: "10.1234/TEST"
Zotero条目键: "ITEM123"
Zotero PDF链接: "zotero://open-pdf/library/items/PDF123"
原文语言: "zh"
中文全文: "[[【原文】测试中文论文.md|中文原文]]"
原文PDF: "[[附件/原文/原文.pdf|原文.pdf]]"
MinerU中文全文: "[[附件/原文/MinerU中文全文.md|MinerU中文全文.md]]"
质量报告: "[[附件/状态/quality-report.json|质量报告]]"
来源锚点: "[[附件/状态/source-anchors.json|来源锚点]]"
---

# 导航
- [质量报告](../附件/状态/quality-report.json)

# 下一步
完成迁移。
""",
        encoding="utf-8",
    )
    (reading / "【原文】测试中文论文.md").write_text(
        """---
翻译状态: 不适用
Zotero PDF链接: "zotero://open-pdf/library/items/PDF123"
---

![[附件/原文/MinerU中文全文.md]]
""",
        encoding="utf-8",
    )
    (source / "MinerU中文全文.md").write_text("中文正文。" * 100, encoding="utf-8")
    (source / "原文.pdf").write_bytes(b"same-pdf")
    (workspace / "附件" / "duplicate.pdf").write_bytes(b"same-pdf")
    (state / "quality-report.json").write_text(
        json.dumps({"paper_workspace": ".", "overall_status": "pass", "source_anchor_status": "pass"}),
        encoding="utf-8",
    )
    (state / "source-anchors.json").write_text("[]", encoding="utf-8")
    (state / "metadata-verification.json").write_text(
        json.dumps({"doi": "10.1234/TEST", "zotero_key": "ITEM123", "verified_at": "2026-07-18T10:00:00+08:00"}),
        encoding="utf-8",
    )
    return workspace


def test_migrate_artifacts_moves_json_and_duplicate_pdf_out_of_vault(tmp_path: Path) -> None:
    workspace = _make_legacy_chinese_workspace(tmp_path)
    artifact_root = tmp_path / "output"
    args = Namespace(
        workspaces=[str(workspace)],
        apply=True,
        backup_root=str(tmp_path / "backup"),
        resolved_locations={
            "artifact_root": artifact_root,
            "paper_root": workspace.parent,
            "vault_root": tmp_path / "vault",
        },
    )

    assert run(args) == 0
    assert list(workspace.rglob("*.json")) == []
    assert list(workspace.rglob("*.pdf")) == [workspace / "附件" / "原文" / "原文.pdf"]
    run_dirs = list(artifact_root.glob("20*"))
    assert len(run_dirs) == 1
    assert len(list((run_dirs[0] / "state").glob("*.json"))) == 3
    overview = next((workspace / "阅读工作台").glob("【总览】*.md")).read_text(encoding="utf-8")
    assert "外部产物ID:" in overview
    assert "quality-report.json" not in overview

