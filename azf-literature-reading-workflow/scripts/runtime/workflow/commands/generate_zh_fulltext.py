from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.markdown_properties import localize_frontmatter_keys
from workflow.services.cache_paths import workspace_cache_root
from workflow.validators.image_links import validate_image_links
from workflow.validators.translation_fidelity import validate_translation_artifact


def run(args) -> int:
    workspace = PaperWorkspace.from_root(Path(args.workspace))
    title_zh = args.title_zh
    parsed = workspace.source_path / "MinerU英文全文.md"
    out_path = workspace.reading_workspace_path / f"【中译】{title_zh}.md"
    translated = Path(args.translated_note).resolve() if args.translated_note else None
    audit = Path(args.translation_audit).resolve() if args.translation_audit else None

    if translated is None or audit is None:
        print(json.dumps({
            "status": "needs_translation",
            "reason": "generate-zh-fulltext no longer creates a summary-style placeholder. Provide --translated-note and --translation-audit from azf-paper-zh-reading-translator.",
            "source": str(parsed),
        }, ensure_ascii=False, indent=2))
        return 2

    issues = validate_translation_artifact(parsed, translated, audit)
    if issues:
        print(json.dumps({"status": "fail", "issues": issues}, ensure_ascii=False, indent=2))
        return 2

    if out_path.exists() and translated != out_path.resolve() and not args.force:
        print(json.dumps({
            "status": "fail",
            "reason": f"existing Chinese translation is user-owned; use --force only after backup and explicit review: {out_path}",
        }, ensure_ascii=False, indent=2))
        return 2

    content = localize_frontmatter_keys(translated.read_text(encoding="utf-8-sig"))
    backup_path: Path | None = None
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and translated != out_path.resolve() and args.force:
            backup_dir = workspace_cache_root(workspace.root_path) / "translation-backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{out_path.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            shutil.copy2(out_path, backup_path)
        if translated != out_path.resolve():
            out_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        audit_target = workspace.root_path / "translation-audit.json"
        if audit != audit_target.resolve():
            shutil.copy2(audit, audit_target)

    image_issues = validate_image_links(out_path) if out_path.exists() else []
    if not args.dry_run:
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.translation_status = "pass"
        report.blocking_issues = [
            issue for issue in report.blocking_issues
            if not any(marker in issue.casefold() for marker in ["translation", "chinese note", "translation-audit"])
        ]
        report.image_link_status = "pass" if not image_issues else "warning"
        report.add_note("Accepted faithful sentence-accounted Chinese translation; no summary or explanatory expansion is allowed in the translation note.")
        save_quality_report(workspace.quality_path, report)

    print(json.dumps({
        "status": "pass",
        "path": str(out_path),
        "dry_run": args.dry_run,
        "translation_mode": "faithful_sentence_by_sentence",
        "backup_path": str(backup_path) if backup_path else None,
        "image_issues": image_issues,
    }, ensure_ascii=False, indent=2))
    return 0
