from __future__ import annotations

import json
import shutil
from pathlib import Path

from workflow.adapters.figure_render_extractor import (
    manual_region_manifest,
    render_page_previews,
    run_manual_region_crop,
    run_pdf_figure_render_extractor,
    write_figure_manifest,
)
from workflow.models.paper import PaperWorkspace
from workflow.models.source_anchor import SourceAnchor
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import resolve_run_from_args
from workflow.services.mineru_visual_crops import render_visual_crops
from workflow.services.source_anchor_registry import SourceAnchorRegistry
from workflow.services.workspace_paths import resolve_workspace_path, workspace_relative_value


def _write_accepted_assets(workspace: PaperWorkspace, manifest: list[dict]) -> None:
    manifest_path = workspace.figure_manifest_path
    normalized_manifest: list[dict] = []
    for item in manifest:
        normalized = dict(item)
        for key in ["file_path", "source_pdf"]:
            if normalized.get(key):
                normalized[key] = workspace_relative_value(workspace.root_path, str(normalized[key]))
        normalized["path_base"] = "paper_workspace"
        normalized_manifest.append(normalized)
    write_figure_manifest(manifest_path, normalized_manifest)
    registry = SourceAnchorRegistry(workspace.source_anchor_path)
    for item in normalized_manifest:
        if item.get("crop_status") != "success" or not item.get("accepted_as_highres_figure", True):
            continue
        file_path = resolve_workspace_path(workspace.root_path, item["file_path"])
        registry.add(
            SourceAnchor(
                anchor_id=item["asset_id"],
                paper_workspace=".",
                source_type=item.get("source_type") or "figure",
                page=item.get("page"),
                figure_label=item.get("figure_label"),
                note_target=f"附件/图片/{file_path.name}",
                confidence="high",
                review_note="Accepted high-resolution PDF-render crop.",
            )
        )
    registry.save()


def run(args) -> int:
    workspace, artifact = resolve_run_from_args(args)
    pdf_path = Path(args.pdf).resolve() if args.pdf else workspace.source_path / "原文.pdf"
    cache_dir = artifact.parser_path / "figures"
    cache_dir.mkdir(parents=True, exist_ok=True)
    report = load_quality_report(workspace.quality_path, str(workspace.root_path))

    if args.manual_regions:
        regions_path = Path(args.manual_regions).resolve()
        workspace.figure_path.mkdir(parents=True, exist_ok=True)
        result = run_manual_region_crop(pdf_path, regions_path, workspace.figure_path, dpi=args.manual_dpi)
        manifest = manual_region_manifest(pdf_path, regions_path, workspace.figure_path, dpi=args.manual_dpi)
        if result.returncode != 0 or not manifest or any(item["crop_status"] != "success" for item in manifest):
            report.figure_crop_status = "fail"
            report.add_blocker("manual figure/table crop failed")
            report.add_note((result.stderr or result.stdout)[-1000:])
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "fail", "stdout": result.stdout, "stderr": result.stderr}, ensure_ascii=False, indent=2))
            return result.returncode or 2
        _write_accepted_assets(workspace, manifest)
        report.figure_crop_status = "pass"
        report.source_anchor_status = "pass"
        report.blocking_issues = [issue for issue in report.blocking_issues if "figure" not in issue.lower()]
        report.add_note("Only manually reviewed paper figures/tables were retained; no preview or MinerU candidate images were saved in the vault.")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "pass", "manifest": str(workspace.figure_manifest_path), "assets": manifest}, ensure_ascii=False, indent=2))
        return 0

    if args.mineru_output:
        mineru_output = Path(args.mineru_output).resolve()
    else:
        auto_candidates = [artifact.parser_path, *artifact.parser_path.rglob("auto")]
        mineru_output = next((item for item in auto_candidates if any(item.glob("*.md")) and any(item.glob("*middle*.json"))), None)
    raw_candidates = sorted(artifact.parser_path.rglob("*middle*.json"))
    raw_json_path = raw_candidates[0] if raw_candidates else None
    legacy_raw = workspace.source_path / "MinerU原始输出.json"
    if not raw_json_path and legacy_raw.exists():
        raw_json_path = legacy_raw

    if args.preview_only:
        previews = render_page_previews(pdf_path, cache_dir / "previews", max_pages=args.max_pages, dpi=args.dpi)
        report.figure_crop_status = "partial"
        report.add_note("Temporary page previews were generated outside the Obsidian vault and are not final figure assets.")
        save_quality_report(workspace.quality_path, report)
        print(json.dumps({"status": "preview", "cache": str(cache_dir / 'previews'), "assets": previews}, ensure_ascii=False, indent=2))
        return 0

    skill_result = run_pdf_figure_render_extractor(
        pdf_path=pdf_path,
        out_root=cache_dir / "figure-skill",
        mode=args.mode,
        mineru_output=mineru_output,
        clarity=args.clarity,
        docker_image=args.docker_image,
    )
    if skill_result.returncode != 0:
        report.add_note(f"pdf-figure-render-extractor candidate stage failed: {(skill_result.stderr or skill_result.stdout)[-500:]}")

    if raw_json_path and raw_json_path.exists():
        candidate_dir = cache_dir / "candidates"
        candidate_manifest_path = cache_dir / "candidate-manifest.json"
        candidate_anchor_path = cache_dir / "candidate-source-anchors.json"
        candidates = render_visual_crops(
            pdf_path=pdf_path,
            raw_json_path=raw_json_path,
            figure_dir=candidate_dir,
            manifest_path=candidate_manifest_path,
            anchor_path=candidate_anchor_path,
            workspace_root=workspace.root_path,
        )
        if candidates and args.accept_auto:
            workspace.figure_path.mkdir(parents=True, exist_ok=True)
            accepted: list[dict] = []
            for item in candidates:
                source_file = Path(item["file_path"])
                target_file = workspace.figure_path / source_file.name
                shutil.copy2(source_file, target_file)
                copied = dict(item)
                copied["file_path"] = str(target_file.resolve())
                copied["accepted_as_highres_figure"] = True
                accepted.append(copied)
            _write_accepted_assets(workspace, accepted)
            report.figure_crop_status = "pass"
            report.source_anchor_status = "pass"
            report.add_note("Reviewed automatic figure/table candidates were explicitly accepted and copied from external cache.")
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "pass", "assets": accepted}, ensure_ascii=False, indent=2))
            return 0
        if candidates:
            report.figure_crop_status = "partial"
            report.source_anchor_status = "warning"
            report.add_note("Figure/table candidates are held outside the vault. Review them, then rerun with --accept-auto or provide --manual-regions.")
            save_quality_report(workspace.quality_path, report)
            print(json.dumps({"status": "review_required", "candidate_cache": str(candidate_dir), "count": len(candidates)}, ensure_ascii=False, indent=2))
            return 0

    previews = render_page_previews(pdf_path, cache_dir / "previews", max_pages=args.max_pages, dpi=args.dpi)
    report.figure_crop_status = "partial"
    report.source_anchor_status = "warning"
    report.add_note("No accepted figure regions were available. Temporary previews remain outside the vault for review.")
    save_quality_report(workspace.quality_path, report)
    print(json.dumps({"status": "review_required", "preview_cache": str(cache_dir / 'previews'), "assets": previews}, ensure_ascii=False, indent=2))
    return 0
