import hashlib
import json
import shutil
from pathlib import Path

import workflow.services.core_layout_migration as migration_module
from workflow.models.paper import PaperSource
from workflow.services.artifact_runs import ensure_artifact_run, promote_artifact_run
from workflow.services.core_layout_migration import migrate_workspace_core_layout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _overview(title: str, *, language: str) -> str:
    mineru_property = (
        'MinerU中文全文: "[[附件/原文/MinerU中文全文.md|MinerU中文全文.md]]"\n'
        if language == "zh"
        else 'MinerU英文全文: "[[附件/原文/MinerU英文全文.md|MinerU英文全文.md]]"\n'
    )
    role = "原文" if language == "zh" else "中译"
    alias = "中文原文" if language == "zh" else "中译笔记"
    return f"""---
笔记类型: 索引
笔记状态: 待整理
论文笔记类型: 论文总览
中文题名: "{title}"
原文语言: {language}
Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"
中文全文: "[[【{role}】{title}.md|{alias}]]"
原文PDF: "[[附件/原文/原文.pdf|原文.pdf]]"
{mineru_property}质量报告: "[[附件/状态/quality-report.json|质量报告]]"
---

# 导航
- 精读：[[【精读】{title}.md|精读]]
- 原文说明中仍会提到【精读】这个词，但它不是导航链接。
- JSON: [[附件/状态/quality-report.json|质量报告]]

# 下一步
"""


def _make_workspace(paper_root: Path, name: str, title: str, *, language: str) -> Path:
    workspace = paper_root / "1_单篇论文" / name
    reading = workspace / "阅读工作台"
    source = workspace / "附件" / "原文"
    state = workspace / "附件" / "状态"
    reading.mkdir(parents=True)
    source.mkdir(parents=True)
    state.mkdir(parents=True)
    (reading / f"【总览】{title}.md").write_text(_overview(title, language=language), encoding="utf-8")
    (source / "原文.pdf").write_bytes(b"%PDF-1.4\nlegacy\n")
    mineru_name = "MinerU中文全文.md" if language == "zh" else "MinerU英文全文.md"
    (source / mineru_name).write_text("# 正文\n\n" + "论文内容。" * 80, encoding="utf-8")
    if language == "zh":
        (reading / f"【原文】{title}.md").write_text(
            "---\n论文笔记类型: 中文原文\n---\n\n# 正文\n\n" + "中文原文内容。" * 80,
            encoding="utf-8",
        )
    else:
        (reading / f"【中译】{title}.md").write_text("translation", encoding="utf-8")
    for role in ["问答", "图表", "精读"]:
        (reading / f"【{role}】{title}.md").write_text(f"legacy {role}", encoding="utf-8")
    (reading / "WLC深度强化学习论文问答汇总.md").write_text("user-owned", encoding="utf-8")
    (state / "quality-report.json").write_text(
        json.dumps({"pdf": "附件/原文/原文.pdf", "mineru": f"附件/原文/{mineru_name}"}, ensure_ascii=False),
        encoding="utf-8",
    )
    return workspace


def test_migration_archives_only_exact_prefix_notes_and_preserves_latest_success(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    workspace = _make_workspace(paper_root, "Paper - 测试论文", "测试论文", language="en")
    custom = workspace / "阅读工作台" / "WLC深度强化学习论文问答汇总.md"
    custom_hash = _sha256(custom)
    inbound = vault / "入口.md"
    inbound.write_text("[[【精读】测试论文]]", encoding="utf-8")
    artifact_root = tmp_path / "artifacts"
    previous_id, previous_state = ensure_artifact_run(
        artifact_root,
        workspace,
        source=PaperSource(doi="10.1000/test"),
        new_run=True,
    )
    (previous_state / "translation-audit.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    promote_artifact_run(artifact_root, workspace, previous_id)
    archive_root = paper_root / "99_归档" / "旧版辅助笔记"
    backup_root = tmp_path / "backup"

    dry_run = migrate_workspace_core_layout(
        workspace,
        paper_root=paper_root,
        artifact_root=artifact_root,
        archive_root=archive_root,
        backup_root=backup_root,
        apply=False,
    )

    archived = [item for item in dry_run.operations if item["kind"] == "archive_auxiliary"]
    assert dry_run.issues == []
    assert len(archived) == 3
    assert any("入口.md" in item["incoming_short_links"] for item in archived if "【精读】" in item["source"])
    assert all(item["incoming_path_links"] == [] for item in archived)

    applied = migrate_workspace_core_layout(
        workspace,
        paper_root=paper_root,
        artifact_root=artifact_root,
        archive_root=archive_root,
        backup_root=backup_root,
        apply=True,
    )

    assert applied.issues == []
    assert applied.artifact_id
    source = workspace / "附件" / "原文"
    assert (source / "【原文】测试论文.pdf").is_file()
    assert (source / "【MinerU原文】测试论文.md").is_file()
    assert not (source / "原文.pdf").exists()
    assert not (workspace / "附件" / "状态").exists()
    for role in ["问答", "图表", "精读"]:
        assert not (workspace / "阅读工作台" / f"【{role}】测试论文.md").exists()
        assert (archive_root / workspace.name / f"【{role}】测试论文.md").is_file()
    assert _sha256(custom) == custom_hash
    assert (backup_root / "1_单篇论文" / workspace.name / "阅读工作台" / "【精读】测试论文.md").is_file()
    overview = (workspace / "阅读工作台" / "【总览】测试论文.md").read_text(encoding="utf-8")
    assert '原文PDF: "[[【原文】测试论文.pdf|原文PDF]]"' in overview
    assert 'MinerU原文: "[[【MinerU原文】测试论文.md|MinerU原文]]"' in overview
    assert "[[附件/" not in overview
    assert "原文说明中仍会提到【精读】这个词" in overview
    assert "quality-report.json" not in overview

    index = json.loads((artifact_root / "index.json").read_text(encoding="utf-8"))
    paper = index["papers"]["doi:10.1000_test"]
    assert paper["latest_successful"] == previous_id
    assert paper["latest_attempt"] == applied.artifact_id
    manifest = json.loads((artifact_root / applied.artifact_id / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "migration_complete"
    migrated_state = json.loads(
        (artifact_root / applied.artifact_id / "state" / "quality-report.json").read_text(encoding="utf-8")
    )
    assert migrated_state["pdf"] == "附件/原文/【原文】测试论文.pdf"
    assert migrated_state["mineru"] == "附件/原文/【MinerU原文】测试论文.md"


def test_chinese_migration_merges_source_and_removes_separate_mineru(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    workspace = _make_workspace(paper_root, "Chinese - 中文论文", "中文论文", language="zh")
    (workspace / "阅读工作台" / "【中译】中文论文.md").write_text(
        "---\nMinerU合并到中文正文: true\n---\n\n"
        "![[附件/原文/MinerU中文全文.md|MinerU 中文全文]]\n",
        encoding="utf-8",
    )

    result = migrate_workspace_core_layout(
        workspace,
        paper_root=paper_root,
        artifact_root=tmp_path / "artifacts",
        archive_root=paper_root / "99_归档" / "旧版辅助笔记",
        backup_root=tmp_path / "backup",
        apply=True,
    )

    assert result.issues == []
    source = workspace / "附件" / "原文"
    assert (source / "【原文】中文论文.pdf").is_file()
    assert not (source / "MinerU中文全文.md").exists()
    assert not any(source.glob("【MinerU原文】*.md"))
    assert not (workspace / "阅读工作台" / "【原文】中文论文.md").exists()
    chinese = workspace / "阅读工作台" / "【中译】中文论文.md"
    content = chinese.read_text(encoding="utf-8")
    assert "MinerU合并到中文正文: true" in content
    assert "论文内容" in content
    assert "中文原文内容" not in content
    overview = (workspace / "阅读工作台" / "【总览】中文论文.md").read_text(encoding="utf-8")
    assert '中文全文: "[[【中译】中文论文.md|中文正文]]"' in overview
    assert "MinerU原文:" not in overview


def test_migration_restores_exact_mineru_bytes_after_rename_side_effect(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    workspace = _make_workspace(paper_root, "Paper - 测试论文", "测试论文", language="en")
    legacy = workspace / "附件" / "原文" / "MinerU英文全文.md"
    expected_hash = _sha256(legacy)
    real_move = shutil.move

    def move_with_frontmatter_side_effect(source, target):
        result = real_move(source, target)
        if Path(source).name == "MinerU英文全文.md":
            Path(target).write_text(
                Path(target).read_text(encoding="utf-8").replace("# 正文", "修改时间: 2099-01-01\n# 正文", 1),
                encoding="utf-8",
            )
        if Path(source).name.startswith("【精读】"):
            Path(target).write_text(
                Path(target).read_text(encoding="utf-8") + "\n修改时间: 2099-01-01\n",
                encoding="utf-8",
            )
        return result

    monkeypatch.setattr(migration_module.shutil, "move", move_with_frontmatter_side_effect)

    result = migrate_workspace_core_layout(
        workspace,
        paper_root=paper_root,
        artifact_root=tmp_path / "artifacts",
        archive_root=paper_root / "99_归档" / "旧版辅助笔记",
        backup_root=tmp_path / "backup",
        apply=True,
    )

    assert result.issues == []
    assert _sha256(workspace / "附件" / "原文" / "【MinerU原文】测试论文.md") == expected_hash
    assert (
        _sha256(paper_root / "99_归档" / "旧版辅助笔记" / workspace.name / "【精读】测试论文.md")
        == hashlib.sha256("legacy 精读".encode("utf-8")).hexdigest()
    )


def test_migration_blocks_path_qualified_inbound_links(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    workspace = _make_workspace(paper_root, "Paper - 测试论文", "测试论文", language="en")
    relative = (workspace / "阅读工作台" / "【精读】测试论文.md").relative_to(vault).as_posix()
    (vault / "入口.md").write_text(f"[[{relative}|精读]]", encoding="utf-8")

    result = migrate_workspace_core_layout(
        workspace,
        paper_root=paper_root,
        artifact_root=tmp_path / "artifacts",
        archive_root=paper_root / "99_归档" / "旧版辅助笔记",
        backup_root=tmp_path / "backup",
        apply=False,
    )

    assert any("path-qualified inbound links" in issue for issue in result.issues)
