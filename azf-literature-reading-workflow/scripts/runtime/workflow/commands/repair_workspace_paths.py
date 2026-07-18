from __future__ import annotations

import json
from pathlib import Path

from workflow.services.artifact_runs import repair_run_binding, resolve_run
from workflow.services.workspace_paths import repair_generated_json, validate_generated_json_paths


def run(args) -> int:
    results = []
    for value in args.workspaces:
        workspace, artifact = resolve_run(
            args.resolved_locations["artifact_root"],
            Path(value),
            artifact_id=args.artifact_id,
            create_if_missing=False,
            paper_root=args.resolved_locations["paper_root"],
        )
        files = []
        errors = []
        files.append(repair_run_binding(
            args.resolved_locations["artifact_root"],
            artifact,
            args.resolved_locations["paper_root"],
            apply=args.apply,
        ))
        for path in sorted(workspace.state_path.glob("*.json")):
            try:
                files.append(repair_generated_json(path, workspace.root_path, apply=args.apply))
                errors.extend({"file": str(path), "error": issue} for issue in validate_generated_json_paths(path, workspace.root_path))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append({"file": str(path), "error": str(exc)})
        results.append({
            "workspace": str(workspace.root_path),
            "mode": "apply" if args.apply else "dry-run",
            "changed_paths": sum(item["changed_paths"] for item in files),
            "files": files,
            "errors": errors,
        })
    payload = {"status": "fail" if any(item["errors"] for item in results) else "pass", "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if payload["status"] == "fail" else 0
