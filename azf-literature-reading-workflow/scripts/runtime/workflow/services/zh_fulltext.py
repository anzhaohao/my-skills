from __future__ import annotations

from workflow.adapters.zh_fulltext_translator import build_translation_pending_note


def build_zh_fulltext(title_en: str, title_zh: str, parsed_markdown, figure_manifest=None) -> str:
    return build_translation_pending_note(title_en)
