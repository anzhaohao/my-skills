from __future__ import annotations

import argparse
import json
import sys

from workflow.commands import (
    confirm_locations,
    doctor,
    extract_highres_figures,
    generate_deep_reading,
    generate_zh_fulltext,
    ingest_paper,
    layout_sanity_check,
    locate,
    migrate_concept_cards,
    optimize_translation_footnotes,
    parse_with_mineru,
    plan_batch,
    validate_pilot,
)
from workflow.services.location_resolution import (
    default_manifest_path,
    default_registry_path,
    ensure_workspace_under_paper_root,
    load_confirmed_locations,
)


def _add_location_manifest(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--location-manifest",
        default=str(default_manifest_path()),
        help="Confirmed second-round location manifest",
    )


def _add_common_workspace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True, help="Paper workspace folder")
    _add_location_manifest(parser)


def _requires_confirmed_locations(args: argparse.Namespace) -> bool:
    if args.command in {"parse-with-mineru", "extract-highres-figures", "validate-pilot"}:
        return True
    if args.command in {"ingest-paper", "generate-zh-fulltext", "generate-deep-reading"}:
        return not args.dry_run
    if args.command == "migrate-concept-cards":
        return bool(args.apply)
    if args.command == "optimize-translation-footnotes":
        return bool(args.apply or getattr(args, "all_translations", False))
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="literature-workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("locate", help="Round 1: resolve and audit all note locations without modifying the vault")
    p.add_argument("--vault-root")
    p.add_argument("--paper-root")
    p.add_argument("--concept-library-root")
    p.add_argument("--template-path")
    p.add_argument("--artifact-root")
    p.add_argument("--registry", default=str(default_registry_path()))
    p.add_argument("--manifest", default=str(default_manifest_path()))
    p.set_defaults(func=locate.run)

    p = sub.add_parser("confirm-locations", help="Round 2 gate: confirm a pending location manifest and update the local registry")
    p.add_argument("--manifest", default=str(default_manifest_path()))
    p.add_argument("--registry")
    p.set_defaults(func=confirm_locations.run)

    p = sub.add_parser("doctor", help="Check local readiness")
    p.add_argument("--vault-root", default="E:/software/Obsidian/安钊锋的外置大脑")
    p.add_argument("--location-manifest", default=str(default_manifest_path()))
    p.add_argument("--mineru-image", default="mineru:latest")
    p.add_argument("--strict", action="store_true", help="Return non-zero unless default new-parse requirements are ready")
    p.add_argument("--reuse-existing", action="store_true", help="With --strict, audit readiness for explicitly declared existing MinerU output instead of requiring Docker")
    p.set_defaults(func=doctor.run)

    p = sub.add_parser("ingest-paper", help="Create or update one paper workspace")
    p.add_argument("--pdf", required=True)
    p.add_argument("--workspace", help="Existing or target paper workspace folder")
    _add_location_manifest(p)
    p.add_argument("--title-en")
    p.add_argument("--title-zh", default="中文题名待定")
    p.add_argument("--author", action="append", help="Repeat for each author")
    p.add_argument("--year")
    p.add_argument("--venue")
    p.add_argument("--doi")
    p.add_argument("--citekey")
    p.add_argument("--zotero-key")
    p.add_argument("--zotero-pdf-key", "--zotero-pdf-attachment-key", dest="zotero_pdf_key", help="Zotero PDF attachment item key for zotero://open-pdf links")
    p.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    p.set_defaults(func=ingest_paper.run)

    p = sub.add_parser("parse-with-mineru", help="Run local Docker MinerU by default; reuse only when existing output was explicitly declared and audited")
    _add_common_workspace(p)
    p.add_argument("--pdf")
    p.add_argument("--mode", choices=["docker-run", "docker", "existing", "reuse"], default="docker-run")
    p.add_argument("--docker-image", default="mineru:latest")
    p.add_argument("--reuse-markdown")
    p.add_argument("--reuse-raw-output")
    p.add_argument("--allow-preview", action="store_true")
    p.set_defaults(func=parse_with_mineru.run)

    p = sub.add_parser("extract-highres-figures", help="Generate accepted figure/table assets; previews stay in external cache")
    _add_common_workspace(p)
    p.add_argument("--pdf")
    p.add_argument("--max-pages", type=int, default=3)
    p.add_argument("--dpi", type=int, default=220)
    p.add_argument("--mode", choices=["docker-run", "docker", "existing", "latest-gradio"], default="existing")
    p.add_argument("--mineru-output")
    p.add_argument("--clarity", choices=["4k", "8k", "dpi", "normal", "preview"], default="4k")
    p.add_argument("--docker-image", default="mineru:latest")
    p.add_argument("--preview-only", action="store_true")
    p.add_argument("--accept-auto", action="store_true", help="Copy reviewed automatic candidates into the paper workspace")
    p.add_argument("--manual-regions", help="Reviewed normalized region JSON; only these figures/tables are retained")
    p.add_argument("--manual-dpi", type=int, default=450)
    p.set_defaults(func=extract_highres_figures.run)

    p = sub.add_parser("layout-sanity-check", help="Check parsed Markdown layout sanity")
    _add_common_workspace(p)
    p.set_defaults(func=layout_sanity_check.run)

    p = sub.add_parser("generate-zh-fulltext", help="Validate and import a faithful sentence-accounted Chinese translation")
    _add_common_workspace(p)
    p.add_argument("--pdf")
    p.add_argument("--title-en")
    p.add_argument("--title-zh", required=True)
    p.add_argument("--translated-note", "--reuse-note", dest="translated_note", help="Faithful sentence-accounted Chinese translation produced by the translation skill")
    p.add_argument("--translation-audit", help="Audit JSON proving source hash and complete sentence accounting")
    p.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=generate_zh_fulltext.run)


    p = sub.add_parser("optimize-translation-footnotes", help="Dry-run or apply original-marker-first Obsidian footnotes to Chinese translation notes")
    p.add_argument("--workspace", help="One paper workspace folder")
    p.add_argument("--all-translations", action="store_true", help="Process every Chinese translation note under the confirmed paper_root")
    _add_location_manifest(p)
    p.add_argument("--apply", action="store_true", help="Write optimized footnotes; dry-run by default")
    p.add_argument("--backup-root", help="External rollback backup root used when --apply writes notes")
    p.set_defaults(func=optimize_translation_footnotes.run)

    p = sub.add_parser("generate-deep-reading", help="Generate or reuse deep-reading note")
    _add_common_workspace(p)
    p.add_argument("--title-zh", required=True)
    p.add_argument("--reuse-note")
    p.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=generate_deep_reading.run)

    p = sub.add_parser("migrate-concept-cards", help="Dry-run, stage, or apply the centralized concept-card migration")
    p.add_argument("--vault-root")
    p.add_argument("--paper-root")
    p.add_argument("--target-root")
    p.add_argument("--template-target")
    _add_location_manifest(p)
    p.add_argument("--report-json")
    p.add_argument("--report-markdown")
    p.add_argument("--staging-root")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--replace-existing", action="store_true", help="Archive and replace a non-empty central concept library")
    p.add_argument("--archive-root", help="Rollback archive outside the Obsidian vault")
    p.add_argument("--archive-sources", action="store_true", help="Move paper-local 扫盲班 folders into the rollback archive after validation")
    p.add_argument("--delete-sources", action="store_true", help="Permanently delete validated paper-local 扫盲班 folders")
    p.set_defaults(func=migrate_concept_cards.run)

    p = sub.add_parser("plan-batch", help="Build a read-only queue for workspaces explicitly declared to have existing MinerU output")
    p.add_argument("workspaces", nargs="+")
    p.add_argument("--output")
    p.set_defaults(func=plan_batch.run)

    p = sub.add_parser("validate-pilot", help="Validate pilot workspaces and clean transient caches on pass")
    p.add_argument("workspaces", nargs="+")
    _add_location_manifest(p)
    p.add_argument("--output", help="Optional path to save the pilot validation JSON report")
    p.add_argument("--keep-cache", action="store_true", help="Retain external cache for debugging")
    p.set_defaults(func=validate_pilot.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if _requires_confirmed_locations(args):
        try:
            locations = load_confirmed_locations(args.location_manifest)
            if hasattr(args, "workspace"):
                if args.command == "ingest-paper" and not args.workspace:
                    raise RuntimeError("non-dry-run ingest requires --workspace under the confirmed paper_root")
                if args.workspace:
                    ensure_workspace_under_paper_root(args.workspace, locations["paper_root"])
            if hasattr(args, "workspaces"):
                for workspace in args.workspaces:
                    ensure_workspace_under_paper_root(workspace, locations["paper_root"])
            args.resolved_locations = locations
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "fail", "reason": str(exc)}, ensure_ascii=False, indent=2))
            return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
