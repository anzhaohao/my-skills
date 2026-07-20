from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from workflow.services.location_resolution import load_confirmed_locations
from workflow.services.translation_footnotes import optimize_translation_footnotes
from workflow.validators.translation_footnotes import validate_translation_footnotes


def _discover_workspaces(paper_root: Path) -> list[Path]:
    prefix = "\u3010\u4e2d\u8bd1\u3011"
    workspaces: list[Path] = []
    for note in sorted(paper_root.rglob("*.md")):
        if note.name.startswith(prefix) and note.parent.name == "\u9605\u8bfb\u5de5\u4f5c\u53f0":
            workspaces.append(note.parents[1])
    return workspaces


def run(args) -> int:
    if not args.workspace and not args.all_translations:
        print(json.dumps({"status": "fail", "reason": "provide --workspace or --all-translations"}, ensure_ascii=False, indent=2))
        return 2
    if args.workspace and args.all_translations:
        print(json.dumps({"status": "fail", "reason": "--workspace and --all-translations are mutually exclusive"}, ensure_ascii=False, indent=2))
        return 2
    locations = getattr(args, "resolved_locations", None)
    if args.all_translations or args.apply:
        locations = locations or load_confirmed_locations(args.location_manifest)
    if args.all_translations:
        workspaces = _discover_workspaces(Path(locations["paper_root"]))
    else:
        workspaces = [Path(args.workspace).resolve()]
    backup_root = Path(args.backup_root).resolve() if args.backup_root else None
    results = []
    overall_issues: list[str] = []
    for workspace in workspaces:
        result = optimize_translation_footnotes(workspace, apply=args.apply, backup_root=backup_root)
        validation_issues = validate_translation_footnotes(Path(result.note_path)) if result.note_path else result.issues
        result.issues.extend(issue for issue in validation_issues if issue not in result.issues)
        if result.issues:
            overall_issues.extend(f"{workspace}: {issue}" for issue in result.issues)
        results.append(asdict(result))
    output = {
        "status": "pass" if not overall_issues else "fail",
        "dry_run": not args.apply,
        "workspace_count": len(workspaces),
        "changed_count": sum(1 for item in results if item.get("changed")),
        "results": results,
        "issues": overall_issues,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not overall_issues else 2
