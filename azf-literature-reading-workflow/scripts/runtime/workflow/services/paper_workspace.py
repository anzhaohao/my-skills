from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.dry_run import DryRunPlan
from workflow.services.generated_boundaries import manual_tail_template
from workflow.services.note_preservation import write_if_missing
from workflow.services.overview_note import render_overview
from workflow.services.source_files import ensure_source_pdf


def create_or_update_workspace(
    workspace_root: Path,
    pdf_path: Path,
    source: PaperSource,
    dry_run: bool = True,
) -> tuple[PaperWorkspace, DryRunPlan]:
    workspace = PaperWorkspace.from_root(workspace_root)
    plan = DryRunPlan(dry_run=dry_run)
    for folder in [workspace.root_path, workspace.reading_workspace_path, workspace.attachment_path, workspace.source_path, workspace.figure_path, workspace.state_path]:
        plan.add_change("mkdir", folder, "paper workspace contract folder")
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)

    target_pdf = workspace.source_path / "原文.pdf"
    plan.add_change("copy", target_pdf, f"copy source PDF from {pdf_path}")
    if not dry_run:
        ensure_source_pdf(pdf_path, workspace.source_path)

    overview = render_overview(source, workspace)
    plan.add_change("write", workspace.overview_note, "Chinese YAML properties and navigation note", workspace.overview_note.exists())
    if not dry_run:
        write_if_missing(workspace.overview_note, overview)

    title_zh = source.title_zh or "中文题名待定"
    placeholders = {
        workspace.reading_workspace_path / f"【中译】{title_zh}.md": "---\n类型: 论文中文全文\n英文题名: \"" + (source.title_en or "") + "\"\n翻译状态: 待逐句忠实翻译\n---\n\n> [!warning] 尚未生成中文全文\n> 必须按原文逐句忠实翻译，不得用摘要、精读或解释代替翻译。\n",
        workspace.reading_workspace_path / f"【精读】{title_zh}.md": "# 核心理解\n\n待补充。\n\n# 方法与证据链\n\n待补充。\n\n# 关键图表\n\n待补充。\n\n# 概念障碍\n\n待补充。\n\n# 对我的启发\n\n待补充。\n\n# 待核对\n\n- [ ] 核对来源锚点\n" + manual_tail_template(),
        workspace.reading_workspace_path / "图表解读.md": "# 图表解读\n\n等待高清图裁剪后补充。\n",
        workspace.reading_workspace_path / "问答复习.md": "# 问答复习\n\n等待精读后生成。\n",
    }
    for path, note_content in placeholders.items():
        plan.add_change("write-if-missing", path, "starter reading workspace note", path.exists())
        if not dry_run:
            write_if_missing(path, note_content)

    if not dry_run:
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.metadata_status = "pass" if source.zotero_key and (source.doi or source.citekey) else "warning"
        report.pdf_status = "pass"
        report.preservation_status = "pass"
        report.add_note("Workspace scaffolded without overwriting existing notes; generated YAML property names are Chinese.")
        save_quality_report(workspace.quality_path, report)

    return workspace, plan