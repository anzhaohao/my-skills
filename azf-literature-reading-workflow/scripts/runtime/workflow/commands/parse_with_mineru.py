from __future__ import annotations

import json
import shutil
from pathlib import Path

from workflow.adapters.mineru_docker import docker_status, pymupdf_preview_parse, run_mineru_docker
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import resolve_run_from_args
from workflow.services.mineru_outputs import attach_mineru_outputs


def run(args) -> int:
    workspace, artifact = resolve_run_from_args(args)
    pdf_path = Path(args.pdf).resolve() if args.pdf else workspace.source_path / "原文.pdf"
    markdown_path = workspace.mineru_markdown_path
    cache_dir = artifact.parser_path / "mineru"
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
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reuse_markdown, markdown_path)
        cached_raw = cache_dir / "reused_middle.json"
        shutil.copy2(reuse_raw, cached_raw)
        report.mineru_status = "pass"
        report.source_language = workspace.source_language
        report.source_fulltext_status = "pass"
        report.blocking_issues = [issue for issue in report.blocking_issues if "MinerU" not in issue]
        report.add_note("Reused previously verified local Docker MinerU Markdown and raw layout output; raw data remains outside the Obsidian vault.")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "pass", "markdown": str(markdown_path), "raw_cache": str(cached_raw)}, ensure_ascii=False, indent=2))
        return 0

    if args.mode == "existing":
        raw_candidates = sorted(artifact.parser_path.rglob("*middle*.json"))
        raw_path = raw_candidates[0] if raw_candidates else None
        legacy_raw = workspace.source_path / "MinerU原始输出.json"
        if markdown_path.exists() and (raw_path or legacy_raw.exists()):
            report.mineru_status = "pass"
            report.source_language = workspace.source_language
            report.source_fulltext_status = "pass"
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
        result = run_mineru_docker(pdf_path, cache_dir, image=args.docker_image)
        if result.returncode == 0:
            mapped = attach_mineru_outputs(cache_dir, workspace.source_path, source_language=workspace.source_language)
            if mapped.get("markdown") and mapped.get("raw_output"):
                report.mineru_status = "pass"
                report.source_language = workspace.source_language
                report.source_fulltext_status = "pass"
                report.add_note(f"Formal Docker MinerU pipeline completed. Only {markdown_path.name} was retained in the vault; raw output and images remain in external cache.")
                save_quality_report(workspace.quality_path, report)
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
        preview_dir = cache_dir / "preview"
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
