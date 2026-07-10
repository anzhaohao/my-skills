from __future__ import annotations

import json
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.markdown_properties import localize_frontmatter_keys
from workflow.services.note_preservation import write_generated_note


def run(args) -> int:
    workspace = PaperWorkspace.from_root(Path(args.workspace))
    title_zh = args.title_zh
    out_path = workspace.reading_workspace_path / f"【精读】{title_zh}.md"
    reused = Path(args.reuse_note).resolve() if args.reuse_note else None
    if reused:
        if not reused.is_file():
            print(json.dumps({"status": "fail", "reason": f"reuse note missing: {reused}"}, ensure_ascii=False, indent=2))
            return 2
        content = localize_frontmatter_keys(reused.read_text(encoding="utf-8-sig"))
    else:
        content = '''# 核心理解

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
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if reused:
            out_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        else:
            write_generated_note(out_path, content, force=args.force)
    report = load_quality_report(workspace.quality_path, str(workspace.root_path))
    report.add_note("Reused previously reviewed deep-reading note." if reused else "Deep-reading scaffold generated with source-review warnings.")
    save_quality_report(workspace.quality_path, report)
    print(json.dumps({"status": "pass" if reused else "preview", "path": str(out_path), "dry_run": args.dry_run}, ensure_ascii=False, indent=2))
    return 0