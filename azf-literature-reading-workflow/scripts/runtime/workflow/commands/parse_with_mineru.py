from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from workflow.adapters.mineru_docker import docker_status, pymupdf_preview_parse, run_mineru_docker
from workflow.models.paper import PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.cache_paths import find_cached_mineru_raw
from workflow.services.artifact_runs import workspace_with_artifacts
from workflow.services.mineru_outputs import attach_mineru_outputs
from workflow.services.zh_fulltext import build_chinese_source_fulltext
from workflow.services.zotero_links import read_workspace_zotero_pdf_link


def _publish_markdown(workspace: PaperWorkspace, accepted: Path) -> Path:
    if workspace.source_language == "zh":
        target = workspace.chinese_fulltext_path()
        content = build_chinese_source_fulltext(
            accepted.read_text(encoding="utf-8-sig", errors="replace"),
            title_zh=workspace.title_zh,
            zotero_pdf=read_workspace_zotero_pdf_link(workspace.overview_note),
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target
    target = workspace.mineru_source_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(accepted, target)
    return target


def run(args) -> int:
    locations = getattr(args, "resolved_locations", {}) or {}
    workspace = workspace_with_artifacts(Path(args.workspace), locations.get("artifact_root"), create=True)
    pdf_path = Path(args.pdf).resolve() if args.pdf else workspace.source_pdf_path()
    parser_dir = workspace.state_path.parent / "parser"
    logs_dir = workspace.state_path.parent / "logs"
    parser_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    accepted_markdown = parser_dir / "accepted-mineru.md"
    command_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    mineru_run_dir = parser_dir / f"mineru-{command_stamp}"
    report = load_quality_report(workspace.quality_path, str(workspace.root_path))

    if args.mode == "reuse":
        reuse_markdown = Path(args.reuse_markdown).resolve() if args.reuse_markdown else None
        reuse_raw = Path(args.reuse_raw_output).resolve() if args.reuse_raw_output else None
        if not reuse_markdown or not reuse_markdown.is_file() or not reuse_raw or not reuse_raw.is_file():
            report.mineru_status = "fail"
            report.add_blocker("reused MinerU Markdown/raw output missing")
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "fail", "reason": "reuse files missing"}, ensure_ascii=False, indent=2))
            return 2
        shutil.copy2(reuse_markdown, accepted_markdown)
        published = _publish_markdown(workspace, accepted_markdown)
        cached_raw = parser_dir / f"reused-middle-{command_stamp}.json"
        shutil.copy2(reuse_raw, cached_raw)
        report.mineru_status = "pass"
        report.blocking_issues = [issue for issue in report.blocking_issues if "MinerU" not in issue]
        report.add_note("Reused previously verified local Docker MinerU Markdown and raw layout output; raw data remains outside the Obsidian vault.")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "pass", "markdown": str(published), "raw_cache": str(cached_raw)}, ensure_ascii=False, indent=2))
        return 0

    if args.mode == "existing":
        markdown_path = workspace.chinese_fulltext_path() if workspace.source_language == "zh" else workspace.mineru_source_path()
        raw_path = next(iter(sorted(parser_dir.rglob("*middle*.json"))), None) or find_cached_mineru_raw(workspace.root_path)
        legacy_raw = workspace.source_path / "MinerU原始输出.json"
        if markdown_path.exists() and (raw_path or legacy_raw.exists()):
            report.mineru_status = "pass"
            report.add_note("Attached existing local MinerU output; raw data is resolved from external cache when available.")
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "pass", "markdown": str(markdown_path), "raw_cache": str(raw_path or legacy_raw)}, ensure_ascii=False, indent=2))
            return 0
        report.mineru_status = "fail"
        report.add_blocker("existing MinerU output requested but missing")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "fail", "reason": "existing MinerU output missing"}, ensure_ascii=False, indent=2))
        return 2

    docker = docker_status()
    if docker.get("available"):
        result = run_mineru_docker(pdf_path, mineru_run_dir, image=args.docker_image)
        (logs_dir / f"mineru-{command_stamp}-stdout.txt").write_text(result.stdout or "", encoding="utf-8")
        (logs_dir / f"mineru-{command_stamp}-stderr.txt").write_text(result.stderr or "", encoding="utf-8")
        if result.returncode == 0:
            mapped = attach_mineru_outputs(mineru_run_dir, parser_dir, target_name=accepted_markdown.name)
            if mapped.get("markdown") and mapped.get("raw_output"):
                auto_dir = Path(mapped["auto_dir"])
                accepted_markdown = Path(mapped["markdown"])
                published = _publish_markdown(workspace, accepted_markdown)
                report.mineru_status = "pass"
                if workspace.source_language == "zh":
                    report.translation_status = "not_applicable"
                    report.add_note("Formal Docker MinerU completed; Chinese source content was merged into 【中译】 and the full parser output remains under external artifact_root.")
                else:
                    report.add_note("Formal Docker MinerU completed; 【MinerU原文】 was retained in the vault and the full parser output remains under external artifact_root.")
                save_quality_report(workspace.quality_path, report)
                mapped["published_markdown"] = str(published)
                mapped["retained_parser"] = str(auto_dir)
                print(json.dumps({"status": "pass", "outputs": mapped}, ensure_ascii=False, indent=2))
                return 0
            report.mineru_status = "partial"
            report.add_note("Docker MinerU command finished but accepted Markdown/raw JSON could not be mapped automatically.")
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "partial", "stdout": result.stdout[-2000:], "outputs": mapped}, ensure_ascii=False, indent=2))
            return 0
        report.mineru_status = "fail"
        report.add_blocker("Docker MinerU command failed")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "fail", "stderr": result.stderr[-2000:]}, ensure_ascii=False, indent=2))
        return result.returncode or 1

    if args.allow_preview:
        preview_dir = parser_dir / f"preview-{command_stamp}"
        pymupdf_preview_parse(pdf_path, preview_dir / "preview.md", preview_dir / "preview.json")
        report.mineru_status = "fail"
        report.add_blocker("Docker MinerU unavailable; PyMuPDF preview created in external cache but not accepted")
        report.add_note(docker.get("reason", "Docker unavailable"))
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "preview", "cache": str(preview_dir), "reason": docker.get("reason")}, ensure_ascii=False, indent=2))
        return 0

    report.mineru_status = "fail"
    report.add_blocker("Docker MinerU unavailable")
    save_quality_report(workspace.quality_path, report)
    print(json.dumps({"status": "fail", "reason": docker.get("reason")}, ensure_ascii=False, indent=2))
    return 2
