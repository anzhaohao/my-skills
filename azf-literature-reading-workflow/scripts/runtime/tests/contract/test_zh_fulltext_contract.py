import hashlib
import json
from pathlib import Path

from workflow.services.zh_fulltext import build_zh_fulltext
from workflow.services.markdown_properties import localize_frontmatter_keys
from workflow.services.zotero_links import ensure_frontmatter_property
from workflow.validators.translation_fidelity import validate_translation_artifact, validate_workspace_translation


def test_zh_fulltext_placeholder_does_not_pretend_to_translate(tmp_path: Path) -> None:
    parsed = tmp_path / "MinerU英文全文.md"
    parsed.write_text("Abstract\nAgentic LLM collectives", encoding="utf-8")
    content = build_zh_fulltext("Title EN", "中文题名", parsed)
    assert "尚未生成中文全文" in content
    assert "解析来源节选" not in content
    assert "阅读导入" not in content
    assert "类型: 论文中文全文" not in content
    assert "笔记类型: 知识" in content
    assert "论文笔记类型: 中文全文" in content
    assert "英文题名:" in content


def test_translation_audit_requires_complete_sentence_accounting(tmp_path: Path) -> None:
    source = tmp_path / "MinerU英文全文.md"
    source.write_text("First sentence. Second sentence.", encoding="utf-8")
    note = tmp_path / "【中译】测试.md"
    note.write_text("---\n笔记类型: 知识\n笔记状态: 可用\n论文笔记类型: 中文全文\n---\n\n# 摘要\n\n" + "这是忠实翻译。" * 80, encoding="utf-8")
    audit = tmp_path / "translation-audit.json"
    audit.write_text(json.dumps({
        "mode": "faithful_sentence_by_sentence",
        "status": "pass",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_sentence_count": 2,
        "accounted_sentence_count": 2,
        "omitted_source_sentences": [],
        "added_explanatory_passages": [],
    }, ensure_ascii=False), encoding="utf-8")
    assert validate_translation_artifact(source, note, audit) == []


def test_workspace_translation_requires_audit(tmp_path: Path) -> None:
    source = tmp_path / "附件" / "原文" / "MinerU英文全文.md"
    source.parent.mkdir(parents=True)
    source.write_text("Source sentence.", encoding="utf-8")
    note = tmp_path / "阅读工作台" / "【中译】测试.md"
    note.parent.mkdir(parents=True)
    note.write_text("这是翻译。" * 80, encoding="utf-8")
    issues = validate_workspace_translation(tmp_path)
    assert any("translation audit missing" in issue for issue in issues)


def test_frontmatter_localization_drops_legacy_type_and_keeps_pdf_link() -> None:
    content = localize_frontmatter_keys(
        """---
type: 论文中文全文
workspace: old
zotero_pdf_link: zotero://open-pdf/library/items/PDF12345
translation_note: "[[【中译】测试.md|中译笔记]]"
---

# 正文
"""
    )
    content = ensure_frontmatter_property(content, "Zotero PDF链接", "zotero://open-pdf/library/items/PDF12345")
    assert "类型:" not in content
    assert "工作区:" not in content
    assert "workspace:" not in content
    assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in content
    assert '中文全文: "[[【中译】测试.md|中译笔记]]"' in content
