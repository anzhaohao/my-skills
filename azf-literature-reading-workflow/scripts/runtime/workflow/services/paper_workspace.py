from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.models.artifact import ArtifactRun
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.dry_run import DryRunPlan
from workflow.services.generated_boundaries import manual_tail_template
from workflow.services.note_preservation import write_if_missing
from workflow.services.overview_note import render_overview
from workflow.services.source_files import ensure_source_pdf
from workflow.services.zotero_links import ZOTERO_PDF_PROPERTY, zotero_pdf_link


def _frontmatter(*, note_type: str, note_status: str = "待整理", extra: dict[str, str] | None = None) -> str:
    lines = [
        "---",
        "笔记类型: 知识",
        f"笔记状态: {note_status}",
        f"论文笔记类型: {note_type}",
    ]
    for key, value in (extra or {}).items():
        lines.append(f'{key}: "{value}"')
    lines.extend(["tags:", "  - 论文精读", "---", ""])
    return "\n".join(lines)


def create_or_update_workspace(
    workspace_root: Path,
    pdf_path: Path,
    source: PaperSource,
    artifact_run: ArtifactRun | None = None,
    dry_run: bool = True,
) -> tuple[PaperWorkspace, DryRunPlan]:
    workspace = PaperWorkspace.from_root(
        workspace_root,
        state_path_override=artifact_run.state_path if artifact_run else None,
        artifact_id=artifact_run.artifact_id if artifact_run else None,
    )
    plan = DryRunPlan(dry_run=dry_run)
    for folder in [
        workspace.root_path,
        workspace.reading_workspace_path,
        workspace.attachment_path,
        workspace.source_path,
        workspace.figure_path,
    ]:
        plan.add_change("mkdir", folder, "paper workspace contract folder")
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)

    target_pdf = workspace.source_path / "原文.pdf"
    plan.add_change("copy", target_pdf, f"copy source PDF from {pdf_path}")
    if not dry_run:
        ensure_source_pdf(pdf_path, workspace.source_path)

    title_zh = source.title_zh or "中文题名待定"
    title_en = source.title_en or ""
    zotero_pdf = zotero_pdf_link(source.zotero_pdf_attachment_key)
    zotero_extra = {ZOTERO_PDF_PROPERTY: zotero_pdf} if zotero_pdf else {}
    overview_path = workspace.overview_note_for_title(title_zh)
    workspace.overview_note = overview_path
    overview = render_overview(source, workspace)
    plan.add_change("write", overview_path, "Chinese YAML properties and navigation note", overview_path.exists())
    if not dry_run:
        write_if_missing(overview_path, overview)

    source_language = "zh" if source.source_language.casefold().startswith("zh") else "en"
    if source_language == "zh":
        fulltext_path = workspace.reading_note_path("原文", title_zh)
        fulltext_placeholder = _frontmatter(
            note_type="中文原文",
            extra={"原文语言": "zh", "翻译状态": "不适用", **zotero_extra},
        ) + "\n> [!warning] 尚未导入中文原文全文\n> MinerU 中文解析通过版面检查后，在此链接完整原文。\n"
    else:
        fulltext_path = workspace.reading_note_path("中译", title_zh)
        fulltext_placeholder = _frontmatter(
            note_type="中文全文",
            extra={"英文题名": title_en, "原文语言": "en", "翻译状态": "待逐句忠实翻译", **zotero_extra},
        ) + "\n> [!warning] 尚未生成中文全文\n> 必须按原文逐句忠实翻译，不得用摘要、精读或解释代替翻译。\n"

    placeholders = {
        fulltext_path: fulltext_placeholder,
        workspace.reading_note_path("精读", title_zh): _frontmatter(note_type="精读笔记", extra=zotero_extra)
        + "\n# 核心理解\n\n待补充。\n\n# 方法与证据链\n\n待补充。\n\n# 关键图表\n\n待补充。\n\n# 概念障碍\n\n待补充。\n\n# 对我的启发\n\n待补充。\n\n# 待核对\n\n- [ ] 核对来源锚点\n"
        + manual_tail_template(),
        workspace.reading_note_path("图表", title_zh): _frontmatter(note_type="图表解读", extra=zotero_extra)
        + "\n等待高清图裁剪后补充。\n",
        workspace.reading_note_path("问答", title_zh): _frontmatter(note_type="问答复习", extra=zotero_extra)
        + "\n等待精读后生成。\n",
    }
    for path, note_content in placeholders.items():
        plan.add_change("write-if-missing", path, "starter reading workspace note", path.exists())
        if not dry_run:
            write_if_missing(path, note_content)

    if not dry_run:
        if artifact_run is None:
            raise RuntimeError("external ArtifactRun is required for a write-enabled ingest")
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.metadata_status = "pass" if source.zotero_key and (source.doi or source.citekey) else "warning"
        report.pdf_status = "pass"
        report.source_language = source_language
        report.translation_status = "not_applicable" if source_language == "zh" else report.translation_status
        report.preservation_status = "pass"
        report.add_note("Workspace scaffolded without overwriting existing notes; generated note names use role-prefixed Chinese titles and bodies omit duplicate title headings.")
        save_quality_report(workspace.quality_path, report)

    return workspace, plan
