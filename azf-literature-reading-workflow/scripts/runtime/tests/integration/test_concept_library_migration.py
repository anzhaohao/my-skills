from pathlib import Path

from workflow.services.concept_library import (
    build_migration_plan,
    rewrite_wikilinks,
    stage_plan,
    validate_staging,
    apply_plan,
)


def _write_card(path: Path, body: str, extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n创建时间: 2026-01-01T10:00\n修改时间: 2026-01-02T10:00\n{extra}---\n{body}\n",
        encoding="utf-8",
    )


def test_concept_migration_merges_duplicates_and_stages_flat_card_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    p1 = paper_root / "Paper A" / "扫盲班"
    p2 = paper_root / "Paper B" / "扫盲班"
    _write_card(
        p1 / "自相位调制.md",
        "# 它是什么意思\n\n定义 A。\n\n# 为什么对本文重要\n\n用途 A。\n\n# 常见误解\n\n- 误解 A。",
    )
    _write_card(
        p2 / "自相位调制.md",
        "# 它是什么意思\n\n这是更完整的自相位调制定义。\n\n# 为什么对这篇论文重要\n\n用途 B。\n\n# 常见翻车点\n\n- 误解 B。",
    )
    _write_card(p2 / "FROG trace.md", "# 它是什么意思\n\n二维测量结果。")
    note = paper_root / "Paper A" / "阅读工作台" / "精读.md"
    note.parent.mkdir(parents=True)
    note.write_text("[[../扫盲班/自相位调制|SPM]]", encoding="utf-8")

    target = vault / "02-Brain Cells" / "99_扫盲班"
    template = vault / "05-Junk Drawer" / "2_模板" / "2.1 Templater" / "概念卡模板.md"
    plan = build_migration_plan(vault, paper_root, target, template)

    assert plan.source_count == 3
    assert plan.canonical_count == 2
    assert list(plan.duplicate_groups) == ["自相位调制"]
    merged = next(card for card in plan.cards if card.name == "自相位调制")
    rendered = merged.render()
    assert "用途 A" in rendered and "用途 B" in rendered
    assert "误解 A" in rendered and "误解 B" in rendered
    assert "状态: \"待核对\"" in rendered
    assert len(merged.frontmatter["相关论文"]) == 2

    staging = tmp_path / "staging"
    stage_plan(plan, staging)
    assert validate_staging(plan, staging) == []
    assert len(list(staging.glob("*.md"))) == 2
    assert not (staging / "入口和索引").exists()
    assert not (staging / "概念卡").exists()


def test_rewrite_explicit_sweeper_wikilink() -> None:
    text = "参见 [[../扫盲班/自相位调制|SPM]] 和 [[相位恢复]]。"
    updated, count = rewrite_wikilinks(text, {"自相位调制": "自相位调制"}, "02-Brain Cells/99_扫盲班")
    assert count == 1
    assert "[[02-Brain Cells/99_扫盲班/自相位调制|SPM]]" in updated
    assert "[[相位恢复]]" in updated

def test_apply_plan_replaces_existing_target_and_archives_sources(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    source = paper_root / "Paper A" / "扫盲班"
    _write_card(source / "相位恢复.md", "# 它是什么意思\n\n恢复相位。")
    target = vault / "02-Brain Cells" / "99_扫盲班"
    target.mkdir(parents=True)
    (target / "legacy.md").write_text("legacy", encoding="utf-8")
    template = vault / "05-Junk Drawer" / "2_模板" / "2.1 Templater" / "概念卡模板.md"
    plan = build_migration_plan(vault, paper_root, target, template)
    archive = tmp_path / "archive"

    result = apply_plan(
        plan,
        replace_existing=True,
        archive_root=archive,
        archive_sources=True,
    )

    assert result["status"] == "pass"
    assert (target / "相位恢复.md").is_file()
    assert not (target / "入口和索引").exists()
    assert not (target / "概念卡").exists()
    assert (archive / "central-library-before-reconcile" / "legacy.md").is_file()
    assert (archive / "paper-local-sweepers" / "Paper A" / "扫盲班" / "相位恢复.md").is_file()
    assert not source.exists()


def test_central_wikilink_is_not_rewritten_again() -> None:
    text = "[[02-Brain Cells/99_扫盲班/自相位调制|SPM]]"
    updated, count = rewrite_wikilinks(text, {"自相位调制": "自相位调制"}, "02-Brain Cells/99_扫盲班")
    assert updated == text
    assert count == 0
