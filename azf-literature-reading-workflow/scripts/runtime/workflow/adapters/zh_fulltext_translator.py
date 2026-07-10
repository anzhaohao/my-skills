from __future__ import annotations


def build_translation_pending_note(title_en: str) -> str:
    """Create a clearly non-accepted placeholder without pretending to translate."""
    return f"""---
类型: 论文中文全文
英文题名: "{title_en}"
翻译状态: 待逐句忠实翻译
---

> [!warning] 尚未生成中文全文
> 本文件不能作为论文翻译交付。必须使用 `azf-paper-zh-reading-translator` 按原文逐句完成翻译，并通过 `translation-audit.json` 校验后，才能标记为正式中译。
"""


# Backward-compatible name for callers that only need a non-accepted scaffold.
def generate_preview_chinese_note(title_en: str, title_zh: str, parsed_markdown, figure_manifest=None) -> str:
    return build_translation_pending_note(title_en)
