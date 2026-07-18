from __future__ import annotations

import json
from pathlib import Path

from workflow.services.cache_paths import cleanup_legacy_workspace_transients, cleanup_workspace_cache
from workflow.services.artifact_runs import mark_run_failed, now_iso, promote_run, resolve_run
from workflow.services.overview_status import update_overview_artifact_status
from workflow.validators.source_anchors import validate_source_anchor_file
from workflow.validators.workspace_cleanliness import validate_workspace_cleanliness
from workflow.validators.workspace_contract import validate_workspace_contract
from workflow.validators.translation_fidelity import validate_workspace_translation


def run(args) -> int:
    workspaces = [Path(item).resolve() for item in args.workspaces]
    results = []
    overall_pass = True
    for workspace in workspaces:
        issues = []
        cleanup_removed: list[str] = []
        artifact = None
        try:
            paper, artifact = resolve_run(
                args.resolved_locations["artifact_root"],
                workspace,
                artifact_id=args.artifact_id,
                create_if_missing=False,
                paper_root=args.resolved_locations["paper_root"],
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            results.append({"workspace": str(workspace), "issues": [str(exc)], "cleanup_removed": [], "status": "fail"})
            overall_pass = False
            continue
        quality = paper.quality_path
        quality_data = None
        if quality.exists():
            quality_data = json.loads(quality.read_text(encoding="utf-8-sig"))
        issues.extend(validate_workspace_contract(workspace, paper=paper))
        issues.extend(validate_source_anchor_file(paper.source_anchor_path, workspace))
        issues.extend(validate_workspace_cleanliness(workspace, paper=paper))
        issues.extend(validate_workspace_translation(workspace, paper=paper))
        if not quality.exists():
            issues.append(f"missing quality report: {quality}")
        elif quality_data and quality_data.get("overall_status") != "pass":
            issues.append(f"quality report not pass: {quality_data.get('overall_status')}")
        if issues:
            overall_pass = False
            if args.promote and artifact is not None:
                mark_run_failed(args.resolved_locations["artifact_root"], artifact, "; ".join(issues[:10]))
        elif quality_data and quality_data.get("overall_status") == "pass" and not args.keep_cache:
            cleanup_removed.extend(cleanup_legacy_workspace_transients(workspace))
        if not issues and args.promote and artifact is not None and quality_data:
            accepted_at = now_iso()
            promote_run(args.resolved_locations["artifact_root"], artifact, quality_status="pass", completed_at=accepted_at)
            update_overview_artifact_status(
                paper.overview_note,
                artifact_id=artifact.artifact_id,
                quality_status="pass",
                source_status=quality_data.get("source_anchor_status", "pass"),
                accepted_at=accepted_at,
            )
        results.append(
            {
                "workspace": str(workspace),
                "artifact_id": artifact.artifact_id if artifact else None,
                "issues": issues,
                "cleanup_removed": cleanup_removed,
                "status": "pass" if not issues else "fail",
            }
        )
    output = {"overall_status": "pass" if overall_pass else "fail", "workspaces": results}
    if getattr(args, "output", None):
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if overall_pass else 2
