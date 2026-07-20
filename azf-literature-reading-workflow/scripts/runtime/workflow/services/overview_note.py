from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.services.zotero_links import zotero_pdf_link


def _vault_relative(path: Path) -> str:
    resolved = path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / ".obsidian").is_dir():
            return resolved.relative_to(parent).as_posix()
    return path.as_posix()


def _wikilink(path: Path, alias: str) -> str:
    return f"[[{_vault_relative(path)}|{alias}]]"


def _note_wikilink(path: Path, alias: str) -> str:
    return f"[[{path.name}|{alias}]]"


def _yaml_list(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return "[]"
    return "\n" + "\n".join(f"  - {value}" for value in cleaned)


def render_overview(source: PaperSource, workspace: PaperWorkspace) -> str:
    title_en = source.title_en or workspace.workspace_name
    title_zh = source.title_zh or "未命名论文"
    authors = ", ".join(source.authors) if source.authors else "未知"
    year = source.year or "未知"
    doi = source.doi or ""
    citekey = source.citekey or ""
    zotero_key = source.zotero_key or ""
    zotero_pdf = zotero_pdf_link(source.zotero_pdf_attachment_key)
    aliases = _yaml_list([title_zh, title_en, citekey])
    zotero_pdf_nav = f"- Zotero PDF: [打开PDF]({zotero_pdf})\n" if zotero_pdf else ""
    zh_fulltext_link = _note_wikilink(workspace.reading_note_path("中译", title_zh), "中译笔记")
    pdf_link = _wikilink(workspace.source_path / "原文.pdf", "原文.pdf")
    mineru_link = _wikilink(workspace.source_path / "MinerU英文全文.md", "MinerU英文全文.md")
    quality_link = _wikilink(workspace.quality_path, "quality-report.json")
    anchors_link = _wikilink(workspace.source_anchor_path, "source-anchors.json")
    return f"""---
笔记类型: 索引
笔记状态: 待整理
论文笔记类型: 论文总览
英文题名: "{title_en}"
中文题名: "{title_zh}"
作者: "{authors}"
年份: "{year}"
期刊: "{source.venue or ''}"
DOI: "{doi}"
引用键: "{citekey}"
Zotero条目键: "{zotero_key}"
Zotero PDF链接: "{zotero_pdf}"
中文全文: "{zh_fulltext_link}"
原文PDF: "{pdf_link}"
MinerU英文全文: "{mineru_link}"
质量报告: "{quality_link}"
来源锚点: "{anchors_link}"
已导入: true
已解析: false
已检查版面: false
已裁剪图表: false
已中译: false
已精读: false
aliases: {aliases}
tags:
  - 论文精读
---
> {title_en}

# 导航
- 阅读工作台: {workspace.reading_workspace_path}
{zotero_pdf_nav}- 原文材料: {pdf_link} / {mineru_link}
- 质量报告: {quality_link}
- 来源锚点: {anchors_link}

# 进度
- 已导入: ✅
- 已解析: ⏳
- 已检查版面: ⏳
- 已裁剪图表: ⏳
- 已中译: ⏳
- 已精读: ⏳

# 下一步
1. 运行 MinerU 解析并检查版面。
2. 生成中文全文与来源锚点。
3. 开始逐句深读卡片。
"""
