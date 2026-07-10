from __future__ import annotations

import json
from pathlib import Path

from workflow.validators.translation_fidelity import validate_workspace_translation


def inspect_workspace(workspace: Path) -> dict:
    workspace = workspace.expanduser().resolve()
    source_pdf = workspace / "附件" / "原文" / "原文.pdf"
    mineru_markdown = workspace / "附件" / "原文" / "MinerU英文全文.md"
    quality_path = workspace / "quality-report.json"
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

    translation_issues = validate_workspace_translation(workspace)
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
        "state": state,
        "next_action": next_action,
        "reuse_mineru": mineru_markdown.is_file(),
        "docker_required": False,
        "blockers": blockers,
        "translation_issues": translation_issues,
    }


def run(args) -> int:
    items = [inspect_workspace(Path(value)) for value in args.workspaces]
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
