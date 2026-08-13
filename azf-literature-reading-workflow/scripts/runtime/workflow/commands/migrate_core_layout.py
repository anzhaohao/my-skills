from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from workflow.services.core_layout_migration import migrate_workspace_core_layout


def run(args) -> int:
    locations = getattr(args, "resolved_locations", {}) or {}
    paper_root = Path(locations["paper_root"]).resolve()
    artifact_root = Path(locations["artifact_root"]).resolve()
    archive_root = Path(args.archive_root).resolve() if args.archive_root else paper_root / "99_归档" / "旧版辅助笔记"
    backup_root = Path(args.backup_root).resolve() if args.backup_root else None
    if args.apply and backup_root is None:
        print(json.dumps({"status": "fail", "reason": "--apply requires --backup-root"}, ensure_ascii=False, indent=2))
        return 2
    if args.apply:
        vault_root = Path(locations["vault_root"]).resolve()
        try:
            backup_root.relative_to(vault_root)
        except ValueError:
            pass
        else:
            print(
                json.dumps(
                    {"status": "fail", "reason": "--backup-root must be outside the Obsidian vault"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
    results = []
    issues: list[str] = []
    for item in args.workspaces:
        try:
            result = migrate_workspace_core_layout(
                Path(item),
                paper_root=paper_root,
                artifact_root=artifact_root,
                archive_root=archive_root,
                backup_root=backup_root or paper_root,
                apply=args.apply,
            )
            results.append(asdict(result))
            issues.extend(f"{item}: {issue}" for issue in result.issues)
        except (OSError, RuntimeError, ValueError) as exc:
            failure = {"workspace": str(Path(item).resolve()), "dry_run": not args.apply, "issues": [str(exc)]}
            results.append(failure)
            issues.append(f"{item}: {exc}")
    payload = {
        "status": "pass" if not issues else "fail",
        "dry_run": not args.apply,
        "archive_root": str(archive_root),
        "workspace_count": len(results),
        "results": results,
        "issues": issues,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 2
