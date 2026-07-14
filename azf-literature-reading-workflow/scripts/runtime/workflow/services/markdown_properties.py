from __future__ import annotations

import re


DEFAULT_PROPERTY_NAMES = {
    "note_type": "笔记类型",
    "note_status": "笔记状态",
    "paper_note_type": "论文笔记类型",
    "title_en": "英文题名",
    "title_zh": "中文题名",
    "authors": "作者",
    "year": "年份",
    "venue": "期刊",
    "doi": "DOI",
    "citekey": "引用键",
    "zotero_key": "Zotero条目键",
    "zotero_pdf_link": "Zotero PDF链接",
    "pdf": "原文PDF",
    "mineru_markdown": "MinerU英文全文",
    "quality_report": "质量报告",
    "source_anchors": "来源锚点",
    "status": "笔记状态",
}

DEFAULT_DROPPED_PROPERTY_NAMES = {"type", "workspace", "zotero_link", "zotero_item_link"}


def localize_frontmatter_keys(text: str, mapping: dict[str, str] | None = None) -> str:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    names = mapping or DEFAULT_PROPERTY_NAMES
    in_frontmatter = True
    remove_indexes: list[int] = []
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            in_frontmatter = False
            break
        if not in_frontmatter or not line or line[0].isspace():
            continue
        match = re.match(r"^([^:#]+):(.*)$", line)
        if match:
            key = match.group(1).strip()
            if key in DEFAULT_DROPPED_PROPERTY_NAMES:
                remove_indexes.append(index)
                continue
            if key in names:
                lines[index] = f"{names[key]}:{match.group(2)}"
    for index in reversed(remove_indexes):
        del lines[index]
    trailing_newline = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + trailing_newline
