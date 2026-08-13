from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import workspace_with_artifacts
from workflow.services.dry_run import DryRunPlan
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
    dry_run: bool = True,
    artifact_root: Path | None = None,
) -> tuple[PaperWorkspace, DryRunPlan]:
    if not source.title_zh or source.title_zh.strip() in {"中文题名待定", "未命名论文"}:
        raise ValueError("中文短标题缺失；写入前必须明确提供 --title-zh")
    if not dry_run and artifact_root is None:
        raise ValueError("write-enabled ingest requires confirmed external artifact_root")
    workspace = workspace_with_artifacts(
        workspace_root,
        artifact_root,
        source=source,
        create=not dry_run,
        new_run=False,
    )
    plan = DryRunPlan(dry_run=dry_run)
    for folder in [
        workspace.root_path,
        workspace.reading_workspace_path,
        workspace.attachment_path,
        workspace.source_path,
    ]:
        plan.add_change("mkdir", folder, "paper workspace contract folder")
        if not dry_run:
            folder.mkdir(parents=True, exist_ok=True)

    title_zh = source.title_zh
    workspace.title_zh = title_zh
    workspace.source_language = source.source_language if source.source_language in {"en", "zh"} else "en"
    target_pdf = workspace.source_pdf_path(title_zh)
    plan.add_change("copy", target_pdf, f"copy source PDF from {pdf_path}")
    if not dry_run:
        ensure_source_pdf(pdf_path, workspace.source_path, copy_name=target_pdf.name)

    title_en = source.title_en or ""
    zotero_pdf = zotero_pdf_link(source.zotero_pdf_attachment_key)
    zotero_extra = {ZOTERO_PDF_PROPERTY: zotero_pdf} if zotero_pdf else {}
    overview_path = workspace.overview_note_for_title(title_zh)
    workspace.overview_note = overview_path
    overview = render_overview(source, workspace)
    plan.add_change("write", overview_path, "Chinese YAML properties and navigation note", overview_path.exists())
    if not dry_run:
        write_if_missing(overview_path, overview)

    translation_status = "等待 MinerU 合并" if source.source_language == "zh" else "待逐句忠实翻译"
    warning = (
        "> [!warning] 尚未生成中文正文\n> 中文原文将在 MinerU 解析后直接合并到本笔记，不另保留 MinerU Markdown。\n"
        if source.source_language == "zh"
        else "> [!warning] 尚未生成中文全文\n> 必须按原文逐句忠实翻译，不得用摘要或解释代替翻译。\n"
    )
    placeholders = {
        workspace.chinese_fulltext_path(title_zh): _frontmatter(
            note_type="中文全文",
            extra={
                "英文题名": title_en,
                "中文短标题": title_zh,
                "原文语言": source.source_language,
                "翻译状态": translation_status,
                **zotero_extra,
            },
        )
        + "\n"
        + warning,
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
        report.add_note("Workspace scaffolded with only overview and Chinese fulltext notes; PDF and English MinerU source use the confirmed Chinese short title.")
        save_quality_report(workspace.quality_path, report)

    return workspace, plan
