from __future__ import annotations

import json
from pathlib import Path

from workflow.services.artifact_runs import resolve_run

from workflow.validators.translation_fidelity import validate_workspace_translation


def inspect_workspace(workspace: Path, *, artifact_root: Path, artifact_id: str | None = None) -> dict:
    workspace = workspace.expanduser().resolve()
    source_pdf = workspace / "附件" / "原文" / "原文.pdf"
    paper, artifact = resolve_run(artifact_root, workspace, artifact_id=artifact_id, create_if_missing=False)
    mineru_markdown = paper.mineru_markdown_path
    quality_path = paper.quality_path
    quality = {}
    if quality_path.is_file():
        quality = json.loads(quality_path.read_text(encoding="utf-8-sig"))

    blockers: list[str] = []
    if not source_pdf.is_file():
        blockers.append("source PDF missing")
    if not mineru_markdown.is_file():
        blockers.append("verified MinerU Markdown missing")
    layout_status = quality.get("layout_sanity_status")
    if layout_status not in {"pass", "not_applicable"}:
        blockers.append(f"layout status is {layout_status or 'missing'}")

    translation_issues = validate_workspace_translation(workspace, paper=paper)
    if blockers:
        next_action = "resolve_blockers"
        state = "blocked"
    elif translation_issues:
        next_action = "retranslate_from_existing_mineru"
        state = "ready"
    elif quality.get("overall_status") != "pass":
        next_action = "rerun_quality_gate"
        state = "ready"
    else:
        next_action = "complete"
        state = "complete"

    return {
        "workspace": str(workspace),
        "artifact_id": artifact.artifact_id,
        "state": state,
        "next_action": next_action,
        "reuse_mineru": mineru_markdown.is_file(),
        "source_language": paper.source_language,
        "docker_required": not mineru_markdown.is_file(),
        "blockers": blockers,
        "translation_issues": translation_issues,
    }


def run(args) -> int:
    artifact_root = args.resolved_locations["artifact_root"]
    items = [inspect_workspace(Path(value), artifact_root=artifact_root, artifact_id=args.artifact_id) for value in args.workspaces]
    payload = {
        "mode": "dry-run",
        "policy": "audit_explicit_existing_mineru",
        "items": items,
        "counts": {
            "total": len(items),
            "ready": sum(item["state"] == "ready" for item in items),
            "blocked": sum(item["state"] == "blocked" for item in items),
            "complete": sum(item["state"] == "complete" for item in items),
        },
    }
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not payload["counts"]["blocked"] else 2
