from __future__ import annotations

import json
from pathlib import Path

from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import resolve_run_from_args
from workflow.services.markdown_properties import localize_frontmatter_keys
from workflow.services.note_preservation import write_generated_note
from workflow.services.zotero_links import ZOTERO_PDF_PROPERTY, ensure_frontmatter_property, read_workspace_zotero_pdf_link


def _deep_reading_frontmatter(zotero_pdf: str = "") -> str:
    lines = [
        "---",
        "笔记类型: 知识",
        "笔记状态: 待整理",
        "论文笔记类型: 精读笔记",
    ]
    if zotero_pdf:
        lines.append(f'{ZOTERO_PDF_PROPERTY}: "{zotero_pdf}"')
    lines.extend(["tags:", "  - 论文精读", "---", ""])
    return "\n".join(lines)


def run(args) -> int:
    workspace, _artifact = resolve_run_from_args(args, require_writable=not args.dry_run)
    title_zh = args.title_zh
    out_path = workspace.reading_note_path("精读", title_zh)
    reused = Path(args.reuse_note).resolve() if args.reuse_note else None
    zotero_pdf = read_workspace_zotero_pdf_link(workspace.overview_note)
    if reused:
        if not reused.is_file():
            print(json.dumps({"status": "fail", "reason": f"reuse note missing: {reused}"}, ensure_ascii=False, indent=2))
            return 2
        content = localize_frontmatter_keys(reused.read_text(encoding="utf-8-sig"))
        for key, value in [
            ("笔记类型", "知识"),
            ("笔记状态", "待整理"),
            ("论文笔记类型", "精读笔记"),
        ]:
            content = ensure_frontmatter_property(content, key, value)
        content = ensure_frontmatter_property(content, ZOTERO_PDF_PROPERTY, zotero_pdf)
    else:
        body = '''# 核心理解

> [!warning] 精读预览
> 当前还没有通过正式 MinerU、高清图裁剪和来源锚点质量门，因此这里只保留精读工作台结构。

# 方法与证据链

待正式解析后补充。

# 关键图表

待高清图裁剪后补充。

# 概念障碍

待与同级扫盲班概念卡关联。

# 对我的启发

待阅读后补充。

# 待核对

- [ ] Docker MinerU 解析
- [ ] 双栏/版面顺序
- [ ] 图表来源锚点
'''
        content = body if out_path.exists() and not args.force else _deep_reading_frontmatter(zotero_pdf) + "\n" + body
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if reused:
            out_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        else:
            if out_path.exists() and not args.force and zotero_pdf:
                existing = out_path.read_text(encoding="utf-8-sig", errors="replace")
                out_path.write_text(ensure_frontmatter_property(existing, ZOTERO_PDF_PROPERTY, zotero_pdf), encoding="utf-8")
            write_generated_note(out_path, content, force=args.force)
    if not args.dry_run:
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.add_note("Reused previously reviewed deep-reading note." if reused else "Deep-reading scaffold generated with source-review warnings.")
        save_quality_report(workspace.quality_path, report)
    print(json.dumps({"status": "pass" if reused else "preview", "path": str(out_path), "dry_run": args.dry_run}, ensure_ascii=False, indent=2))
    return 0
