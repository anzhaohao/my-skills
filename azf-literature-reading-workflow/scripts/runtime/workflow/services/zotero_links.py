from __future__ import annotations

from pathlib import Path


ZOTERO_PDF_PROPERTY = "Zotero PDF链接"
ZOTERO_ITEM_LINK_PROPERTY = "Zotero条目链接"


def zotero_pdf_link(attachment_key: str | None) -> str:
    key = (attachment_key or "").strip()
    return f"zotero://open-pdf/library/items/{key}" if key else ""


def extract_frontmatter_value(text: str, key: str) -> str:
    text = text.lstrip("\ufeff")
    if not text.startswith("---") or text.count("---") < 2:
        return ""
    frontmatter = text.split("---", 2)[1]
    for line in frontmatter.splitlines():
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def read_workspace_zotero_pdf_link(overview_note: Path) -> str:
    if not overview_note.is_file():
        return ""
    return extract_frontmatter_value(overview_note.read_text(encoding="utf-8-sig", errors="replace"), ZOTERO_PDF_PROPERTY)


def ensure_frontmatter_property(text: str, key: str, value: str) -> str:
    if not value:
        return text
    text = text.lstrip("\ufeff")
    if not text.startswith("---") or text.count("---") < 2:
        return f"---\n{key}: \"{value}\"\n---\n\n{text.lstrip()}"
    _before, frontmatter, body = text.split("---", 2)
    lines = frontmatter.strip("\n").splitlines()
    rendered = f'{key}: "{value}"'
    for index, line in enumerate(lines):
        if line.startswith(key + ":"):
            lines[index] = rendered
            break
    else:
        insert_at = len(lines)
        for marker in ["tags:", "aliases:"]:
            for index, line in enumerate(lines):
                if line.startswith(marker):
                    insert_at = index
                    break
            if insert_at != len(lines):
                break
        for index, line in enumerate(lines):
            if line.startswith("Zotero条目键:"):
                insert_at = index + 1
                break
        lines.insert(insert_at, rendered)
    return "---\n" + "\n".join(lines).rstrip() + "\n---" + body
