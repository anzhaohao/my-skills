from __future__ import annotations

from workflow.adapters.zh_fulltext_translator import build_translation_pending_note


def build_zh_fulltext(title_en: str, title_zh: str, parsed_markdown, figure_manifest=None) -> str:
    return build_translation_pending_note(title_en)


def build_chinese_source_fulltext(
    mineru_markdown: str,
    *,
    title_zh: str,
    zotero_pdf: str = "",
) -> str:
    """Merge a Chinese-source MinerU result into the canonical Chinese fulltext note."""
    text = mineru_markdown.lstrip("\ufeff")
    if text.startswith("---") and text.count("---") >= 2:
        text = text.split("---", 2)[2].lstrip()
    zotero_line = f'Zotero PDF链接: "{zotero_pdf}"\n' if zotero_pdf else ""
    return (
        "---\n"
        "笔记类型: 知识\n"
        "笔记状态: 可用\n"
        "论文笔记类型: 中文全文\n"
        f'中文短标题: "{title_zh}"\n'
        "原文语言: zh\n"
        "中译适用: false\n"
        "MinerU合并到中文正文: true\n"
        f"{zotero_line}"
        "tags:\n"
        "  - 论文精读\n"
        "---\n\n"
        + text.rstrip()
        + "\n"
    )
