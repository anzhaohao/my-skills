from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.services.wikilinks import short_wikilink
from workflow.services.zotero_links import zotero_pdf_link


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
    source_language = source.source_language if source.source_language in {"en", "zh"} else "en"
    aliases = _yaml_list([title_zh, title_en, citekey])
    zotero_pdf_nav = f"- Zotero PDF: [打开PDF]({zotero_pdf})\n" if zotero_pdf else ""
    zh_alias = "中文正文" if source_language == "zh" else "中译笔记"
    zh_fulltext_link = short_wikilink(workspace.chinese_fulltext_path(title_zh), zh_alias)
    pdf_link = short_wikilink(workspace.source_pdf_path(title_zh), "原文PDF")
    mineru_link = short_wikilink(workspace.mineru_source_path(title_zh), "MinerU原文")
    mineru_property = f'MinerU原文: "{mineru_link}"\n' if source_language == "en" else ""
    mineru_nav = f" / {mineru_link}" if source_language == "en" else ""
    return f"""---
笔记类型: 索引
笔记状态: 待整理
论文笔记类型: 论文总览
英文题名: "{title_en}"
中文题名: "{title_zh}"
中文短标题: "{title_zh}"
原文语言: {source_language}
作者: "{authors}"
年份: "{year}"
期刊: "{source.venue or ''}"
DOI: "{doi}"
引用键: "{citekey}"
Zotero条目键: "{zotero_key}"
Zotero PDF链接: "{zotero_pdf}"
中文全文: "{zh_fulltext_link}"
原文PDF: "{pdf_link}"
{mineru_property}中译适用: {str(source_language == 'en').lower()}
MinerU合并到中文正文: {str(source_language == 'zh').lower()}
外部产物ID: "{workspace.artifact_id or ''}"
质量状态: 待验收
来源核对状态: 待核对
最近验收时间: ""
已导入: true
已解析: false
已检查版面: false
已中译: false
aliases: {aliases}
tags:
  - 论文精读
---
> {title_en}

# 导航
{zotero_pdf_nav}- 原文材料: {pdf_link}{mineru_nav}
- 中文正文: {zh_fulltext_link}

# 进度
- 已导入: ✅
- 已解析: ⏳
- 已检查版面: ⏳
- 已中译: ⏳

# 下一步
1. 运行 MinerU 解析并检查版面。
2. {'把 MinerU 中文正文合并到中文全文笔记。' if source_language == 'zh' else '完成逐句忠实中译并通过审计。'}
3. 运行质量验收；精读、图表和问答仅在明确需要时生成。
"""
