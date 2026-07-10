from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace


def render_overview(source: PaperSource, workspace: PaperWorkspace) -> str:
    title_en = source.title_en or workspace.workspace_name
    title_zh = source.title_zh or "中文题名待定"
    authors = ", ".join(source.authors) if source.authors else "待补充"
    year = source.year or "待补充"
    doi = source.doi or ""
    citekey = source.citekey or ""
    zotero_key = source.zotero_key or ""
    return f'''---
类型: 论文总览
英文题名: "{title_en}"
中文题名: "{title_zh}"
作者: "{authors}"
年份: "{year}"
期刊: "{source.venue or ''}"
DOI: "{doi}"
引用键: "{citekey}"
Zotero条目键: "{zotero_key}"
工作区: "{workspace.root_path.as_posix()}"
原文PDF: "../附件/原文/原文.pdf"
MinerU英文全文: "../附件/原文/MinerU英文全文.md"
质量报告: "../quality-report.json"
来源锚点: "../source-anchors.json"
处理状态:
  已导入: true
  已解析: false
  已检查版面: false
  已裁剪图表: false
  已中译: false
  已精读: false
---

# {title_zh}

## 文献信息

- 英文题名：{title_en}
- 作者：{authors}
- 年份：{year}
- 期刊：{source.venue or '待补充'}
- DOI：{doi or '待补充'}
- Zotero：{zotero_key or '待补充'}

## 一句话理解

待阅读后补充。

## 为什么读

待补充：这篇文献和当前研究问题、方法或概念障碍的关系。

## 导航

- [[【中译】{title_zh}]]
- [[【精读】{title_zh}]]
- [[图表解读]]
- [[问答复习]]
- [原文 PDF](../附件/原文/原文.pdf)
- [MinerU 英文全文](../附件/原文/MinerU英文全文.md)

## 待办与备注

- [ ] 核对 Zotero 元数据
- [ ] 核对 MinerU 双栏排版
- [ ] 核对高清图片裁剪
'''


def reading_note_path(workspace: PaperWorkspace, title_zh: str, kind: str) -> Path:
    return workspace.reading_workspace_path / f"【{kind}】{title_zh}.md"