from pathlib import Path

from workflow.services.concept_card_migration import (
    build_canonical_cards,
    discover_source_cards,
    rewrite_concept_links,
    validate_central_cards,
    write_canonical_cards,
)


def test_concept_card_migration_merges_duplicates_and_rewrites_links(tmp_path: Path) -> None:
    paper_root = tmp_path / "papers"
    for paper, body in [("Paper A", "# 解释\n\nA 的内容。"), ("Paper B", "# 解释\n\nB 的独有内容。")]:
        folder = paper_root / paper / "扫盲班"
        folder.mkdir(parents=True)
        (folder / "相位恢复.md").write_text(f"---\n创建时间: 2026-01-01\n修改时间: 2026-01-02\n---\n{body}\n", encoding="utf-8")

    cards = discover_source_cards(paper_root)
    target = tmp_path / "central" / "概念卡"
    canonical, names, near = build_canonical_cards(cards, target)

    assert len(cards) == 2
    assert len(canonical) == 1
    assert canonical[0].status == "待合并"
    assert len(canonical[0].metadata["相关论文"]) == 2
    assert near == []

    write_canonical_cards(canonical, names, "02-Brain Cells/99_Mind Palace/1_扫盲班/概念卡")
    assert validate_central_cards(target, 1) == []
    text = (target / "相位恢复.md").read_text(encoding="utf-8")
    assert "B 的独有内容" in text or "A 的内容" in text

    rewritten, count = rewrite_concept_links("[[../扫盲班/相位恢复|相位恢复]] 和 [[相位恢复]]", names, "02-Brain Cells/99_Mind Palace/1_扫盲班/概念卡")
    assert count == 2
    assert rewritten.count("02-Brain Cells/99_Mind Palace/1_扫盲班/概念卡/相位恢复") == 2