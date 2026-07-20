from __future__ import annotations

import hashlib
import json
from pathlib import Path

from workflow.services.translation_footnotes import optimize_translation_footnotes
from workflow.validators.translation_footnotes import validate_translation_footnotes
from workflow.validators.translation_fidelity import validate_translation_artifact
from workflow.cli import main as workflow_main

ZH_NOTE = "【中译】测试.md"
ATTACH = "附件"
ORIGINAL = "原文"
STATE = "状态"
READING = "阅读工作台"
MINERU_EN = "MinerU英文全文.md"


def _audit_for(source: Path, audit: Path) -> None:
    audit.write_text(json.dumps({
        "mode": "faithful_sentence_by_sentence",
        "status": "pass",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_sentence_count": 1,
        "accounted_sentence_count": 1,
        "omitted_source_sentences": [],
        "added_explanatory_passages": [],
    }, ensure_ascii=False), encoding="utf-8")


def _workspace_with_note(tmp_path: Path, body: str) -> tuple[Path, Path, Path]:
    workspace = tmp_path
    source = workspace / ATTACH / ORIGINAL / MINERU_EN
    source.parent.mkdir(parents=True)
    source.write_text("Source sentence.", encoding="utf-8")
    state = workspace / ATTACH / STATE
    state.mkdir(parents=True)
    _audit_for(source, state / "translation-audit.json")
    note = workspace / READING / ZH_NOTE
    note.parent.mkdir(parents=True)
    note.write_text(body, encoding="utf-8")
    return workspace, source, note


def test_translation_footnotes_detect_missing_definition(tmp_path: Path) -> None:
    note = tmp_path / ZH_NOTE
    note.write_text("正文[^missing]\n", encoding="utf-8")
    issues = validate_translation_footnotes(note)
    assert "footnote reference missing definition: missing" in issues


def test_translation_footnotes_reject_anchor_inside_formula(tmp_path: Path) -> None:
    note = tmp_path / ZH_NOTE
    note.write_text("$$\na=b[^bad]\n$$\n\n[^bad]: 原文参考文献 [1]：说明。\n", encoding="utf-8")
    issues = validate_translation_footnotes(note)
    assert any("inside LaTeX formula block" in issue for issue in issues)


def test_optimize_translation_footnotes_ignores_author_affiliations(tmp_path: Path) -> None:
    workspace, source, note = _workspace_with_note(tmp_path, """---
笔记类型: 知识
笔记状态: 可用
论文笔记类型: 中文全文
---

张三<sup>1</sup>、李四<sup>2</sup>

<sup>1</sup> 单位一；<sup>2</sup> 单位二
\\*通讯作者：a@example.com

# 摘要

这是一段没有正文参考文献标号的忠实翻译。正文。正文。为了让全文契约验证关注脚注逻辑而不是误判样例过短，这里补入足够长度的中文正文。本文继续描述方法、实验、结果和限制条件，保持普通论文中译的正文长度。这里不新增任何正文参考文献标号，也不触碰作者机构区。后续句子只是测试材料，用来确认翻译全文验证器不会因为样例太短而失败。研究背景、方法说明、实验设置、结果讨论和结论边界都以中文描述，形成一个足够长但语义中性的测试段落。

# 参考文献

1. Reference A.
""")
    result = optimize_translation_footnotes(workspace, apply=True, backup_root=tmp_path / "backup")
    updated = note.read_text(encoding="utf-8")
    assert not result.changed
    assert "# 参考文献脚注" not in updated
    assert "<sup>1</sup> 单位一" in updated
    assert "\\*通讯作者" in updated
    assert validate_translation_footnotes(note) == []
    assert validate_translation_artifact(source, note, tmp_path / ATTACH / STATE / "translation-audit.json") == []


def test_optimize_translation_footnotes_adds_body_reference_citation_definitions(tmp_path: Path) -> None:
    workspace, source, note = _workspace_with_note(tmp_path, """---
笔记类型: 知识
笔记状态: 可用
论文笔记类型: 中文全文
---

作者<sup>1</sup>

<sup>1</sup> 作者单位，必须保留原样。

# 摘要

摘要里出现背景性引用 [1] 时，也属于本命令的处理范围。

# 正文

已有研究表明该方法有效 [1]，并且后续工作扩展了它 [2,3]。另一个范围引用见 [1]-[3]。为了让全文契约验证关注正文参考文献脚注化，而不是误判样例过短，这里补入足够长度的中文正文。本文继续描述方法、实验、结果和限制条件，保持普通论文中译的正文长度。这里的补充句子不改变引用标号，也不触碰作者机构区。后续内容只是测试材料，用来确认脚注锚点与文末定义能够在较完整的中文段落中稳定工作。

$$
y = f(x) [1]
$$

# 参考文献

1. First reference.
2. Second reference.
3. Third reference.
""")
    result = optimize_translation_footnotes(workspace, apply=True, backup_root=tmp_path / "backup")
    updated = note.read_text(encoding="utf-8")
    assert result.changed
    assert "摘要里出现背景性引用 [^1]" in updated
    assert "已有研究表明该方法有效 [^1]" in updated
    assert "后续工作扩展了它 [^2][^3]" in updated
    assert "另一个范围引用见 [^1][^2][^3]" in updated
    assert "[^azf-ref-" not in updated
    assert "<!-- azf-footnotes:" not in updated
    assert "<sup>1</sup> 作者单位，必须保留原样。" in updated
    assert "y = f(x) [1]" in updated
    assert "# 参考文献脚注" not in updated
    assert "# 参考文献" in updated
    assert "[^1]: 原文参考文献 [1]：First reference." in updated
    assert "[^2]: 原文参考文献 [2]：Second reference." in updated
    assert "[^3]: 原文参考文献 [3]：Third reference." in updated
    assert "\n1. First reference." not in updated
    assert "\n2. Second reference." not in updated
    assert "\n3. Third reference." not in updated
    assert "原文参考文献 [1]：First reference." in updated
    assert "原文参考文献 [2]：Second reference." in updated
    assert "原文参考文献 [3]：Third reference." in updated
    assert validate_translation_footnotes(note) == []
    assert validate_translation_artifact(source, note, tmp_path / ATTACH / STATE / "translation-audit.json") == []
    second = optimize_translation_footnotes(workspace, apply=False)
    assert not second.changed


def test_optimize_translation_footnotes_workspace_dry_run_does_not_require_manifest(tmp_path: Path) -> None:
    workspace, _source, _note = _workspace_with_note(tmp_path, "---\n笔记类型: 知识\n---\n\n作者\n\n# 摘要\n这是一段足够长的中译正文。" + "正文。" * 120)
    missing_manifest = tmp_path / "missing-location-manifest.json"
    code = workflow_main([
        "optimize-translation-footnotes",
        "--workspace",
        str(workspace),
        "--location-manifest",
        str(missing_manifest),
    ])
    assert code == 0


def test_optimize_translation_footnotes_migrates_legacy_reference_footnote_section(tmp_path: Path) -> None:
    workspace, _source, note = _workspace_with_note(tmp_path, """---
笔记类型: 知识
---

# 正文

正文引用 [^1]，这里继续补充足够多的中文正文，保证验证器关注脚注迁移逻辑而不是样例长度。本文继续描述方法、实验、结果和限制条件，保持普通论文中译的正文长度。这里的补充句子不改变引用标号，也不触碰作者机构区。

# 参考文献脚注

<!-- azf-footnotes:managed-start -->
[^1]: 原文参考文献 [1]：Legacy reference.
<!-- azf-footnotes:managed-end -->
""")
    result = optimize_translation_footnotes(workspace, apply=True, backup_root=tmp_path / "backup")
    updated = note.read_text(encoding="utf-8")
    assert result.changed
    assert "# 参考文献脚注" not in updated
    assert "<!-- azf-footnotes:" not in updated
    assert "# 参考文献" in updated
    assert "[^1]: 原文参考文献 [1]：Legacy reference." in updated
    assert validate_translation_footnotes(note) == []
