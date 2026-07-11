from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace


def _vault_relative(path: Path) -> str:
    resolved = path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / ".obsidian").is_dir():
            return resolved.relative_to(parent).as_posix()
    return path.as_posix()


def _wikilink(path: Path, alias: str) -> str:
    return f"[[{_vault_relative(path)}|{alias}]]"


def render_overview(source: PaperSource, workspace: PaperWorkspace) -> str:
    title_en = source.title_en or workspace.workspace_name
    title_zh = source.title_zh or "未命名论文"
    authors = ", ".join(source.authors) if source.authors else "未知"
    year = source.year or "未知"
    doi = source.doi or ""
    citekey = source.citekey or ""
    zotero_key = source.zotero_key or ""
    pdf_link = _wikilink(workspace.source_path / "原文.pdf", "原文.pdf")
    mineru_link = _wikilink(workspace.source_path / "MinerU英文全文.md", "MinerU英文全文.md")
    quality_link = _wikilink(workspace.quality_path, "quality-report.json")
    anchors_link = _wikilink(workspace.source_anchor_path, "source-anchors.json")
    return f"""---
类型: 论文总览
英文题名: "{title_en}"
中文题名: "{title_zh}"
作者: "{authors}"
年份: "{year}"
期刊: "{source.venue or ''}"
DOI: "{doi}"
引用键: "{citekey}"
Zotero条目键: "{zotero_key}"
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
---
# {title_zh}

> {title_en}

## 导航
- 阅读工作台: {workspace.reading_workspace_path}
- 原文材料: {pdf_link} / {mineru_link}
- 质量报告: {quality_link}
- 来源锚点: {anchors_link}

## 进度
- 已导入: ?
- 已解析: ?
- 已检查版面: ?
- 已中译: ?
- 已精读: ?

## 下一步
1. 运行 MinerU 解析并检查版面。
2. 生成中文全文与来源锚点。
3. 开始逐句深读卡片。
"""
