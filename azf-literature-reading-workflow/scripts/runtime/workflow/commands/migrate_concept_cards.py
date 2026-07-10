from __future__ import annotations

import json
from pathlib import Path

from workflow.services.concept_library import (
    apply_plan,
    build_migration_plan,
    stage_plan,
    validate_staging,
    write_report,
)
from workflow.services.location_resolution import resolve_locations


def _resolved(value: str | None) -> Path | None:
    return Path(value).expanduser().resolve() if value else None


def _command_locations(args) -> dict[str, Path]:
    confirmed = getattr(args, "resolved_locations", None)
    explicit = {
        "vault_root": _resolved(args.vault_root),
        "paper_root": _resolved(args.paper_root),
        "concept_library_root": _resolved(args.target_root),
        "template_path": _resolved(args.template_target),
    }
    if confirmed:
        for role, path in explicit.items():
            if path is not None and path != confirmed[role]:
                raise RuntimeError(f"explicit {role} differs from the confirmed location manifest")
        return confirmed

    resolution = resolve_locations(
        vault_root=args.vault_root,
        paper_root=args.paper_root,
        concept_library_root=args.target_root,
        template_path=args.template_target,
    )
    if resolution.errors:
        raise RuntimeError("; ".join(resolution.errors))
    return resolution.locations


def run(args) -> int:
    try:
        locations = _command_locations(args)
    except RuntimeError as exc:
        print(json.dumps({"status": "fail", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    vault_root = locations["vault_root"]
    paper_root = locations["paper_root"]
    target_root = locations["concept_library_root"]
    template_target = locations["template_path"]
    archive_root = _resolved(args.archive_root)

    if args.archive_sources and args.delete_sources:
        print(json.dumps({"status": "fail", "reason": "--archive-sources and --delete-sources are mutually exclusive"}, ensure_ascii=False, indent=2))
        return 2
    if (args.replace_existing or args.archive_sources) and archive_root is None:
        print(json.dumps({"status": "fail", "reason": "--archive-root is required for replacement or source archival"}, ensure_ascii=False, indent=2))
        return 2
    if archive_root is not None:
        try:
            archive_root.relative_to(vault_root)
        except ValueError:
            pass
        else:
            print(json.dumps({"status": "fail", "reason": "rollback archive must be outside the Obsidian vault"}, ensure_ascii=False, indent=2))
            return 2

    plan = build_migration_plan(vault_root, paper_root, target_root, template_target)

    if args.report_json and args.report_markdown:
        write_report(plan, Path(args.report_json).resolve(), Path(args.report_markdown).resolve())

    staging_issues: list[str] = []
    if args.staging_root:
        staging_root = Path(args.staging_root).resolve()
        stage_plan(plan, staging_root)
        staging_issues = validate_staging(plan, staging_root)

    if not args.apply:
        payload = {
            "status": "dry-run",
            "source_count": plan.source_count,
            "canonical_count": plan.canonical_count,
            "duplicate_group_count": len(plan.duplicate_groups),
            "link_rewrite_file_count": len(plan.link_rewrites),
            "non_markdown_files": plan.non_markdown_files,
            "staging_issues": staging_issues,
            "locations": {name: str(path) for name, path in locations.items()},
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not staging_issues and not plan.non_markdown_files else 2

    if staging_issues:
        print(json.dumps({"status": "fail", "staging_issues": staging_issues}, ensure_ascii=False, indent=2))
        return 2

    try:
        result = apply_plan(
            plan,
            replace_existing=args.replace_existing,
            archive_root=archive_root,
            archive_sources=args.archive_sources,
            delete_sources=args.delete_sources,
        )
    except RuntimeError as exc:
        print(json.dumps({"status": "fail", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0