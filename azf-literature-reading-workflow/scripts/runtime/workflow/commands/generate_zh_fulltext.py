from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import resolve_run_from_args
from workflow.services.markdown_properties import localize_frontmatter_keys
from workflow.services.cache_paths import workspace_cache_root
from workflow.services.zotero_links import ZOTERO_PDF_PROPERTY, ensure_frontmatter_property, read_workspace_zotero_pdf_link
from workflow.services.workspace_paths import repair_generated_json
from workflow.validators.image_links import validate_image_links
from workflow.validators.translation_fidelity import validate_translation_artifact


def _vault_relative(path: Path) -> str:
    resolved = path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / ".obsidian").is_dir():
            return resolved.relative_to(parent).as_posix()
    return path.as_posix()


def _generate_chinese_source_note(workspace: PaperWorkspace, title_zh: str, *, dry_run: bool, force: bool) -> tuple[int, dict]:
    parsed = workspace.mineru_markdown_path
    out_path = workspace.reading_note_path("原文", title_zh)
    if not parsed.is_file():
        return 2, {"status": "fail", "reason": f"Chinese MinerU source missing: {parsed}"}
    if out_path.exists() and not force:
        existing = out_path.read_text(encoding="utf-8-sig", errors="replace")
        if "尚未导入中文原文全文" not in existing and parsed.name not in existing:
            return 2, {"status": "fail", "reason": f"existing Chinese source note is user-owned; review before --force: {out_path}"}
    zotero_pdf = read_workspace_zotero_pdf_link(workspace.overview_note)
    content = "\n".join([
        "---",
        "笔记类型: 知识",
        "笔记状态: 可用",
        "论文笔记类型: 中文原文",
        "原文语言: zh",
        "翻译状态: 不适用",
        f'Zotero PDF链接: "{zotero_pdf}"',
        "tags:",
        "  - 论文精读",
        "---",
        "",
        f'![[{_vault_relative(parsed)}|MinerU 中文全文]]',
        "",
    ])
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.source_language = "zh"
        report.source_fulltext_status = "pass"
        report.translation_status = "not_applicable"
        report.blocking_issues = [issue for issue in report.blocking_issues if "translation" not in issue.casefold() and "chinese note" not in issue.casefold()]
        report.add_note("Chinese source paper uses a linked MinerU Chinese fulltext note; translation is not applicable.")
        save_quality_report(workspace.quality_path, report)
    return 0, {"status": "pass", "path": str(out_path), "dry_run": dry_run, "translation_mode": "not_applicable"}


def run(args) -> int:
    workspace, artifact = resolve_run_from_args(args, require_writable=not args.dry_run)
    title_zh = args.title_zh
    if workspace.source_language == "zh":
        code, payload = _generate_chinese_source_note(workspace, title_zh, dry_run=args.dry_run, force=args.force)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return code
    parsed = workspace.mineru_markdown_path
    out_path = workspace.reading_note_path("中译", title_zh)
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
    for key, value in [
        ("笔记类型", "知识"),
        ("笔记状态", "可用"),
        ("论文笔记类型", "中文全文"),
    ]:
        content = ensure_frontmatter_property(content, key, value)
    zotero_pdf = read_workspace_zotero_pdf_link(workspace.overview_note)
    content = ensure_frontmatter_property(content, ZOTERO_PDF_PROPERTY, zotero_pdf)
    backup_path: Path | None = None
    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and translated != out_path.resolve() and args.force:
            backup_dir = artifact.logs_path / "translation-backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{out_path.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
            shutil.copy2(out_path, backup_path)
        if translated != out_path.resolve() or out_path.read_text(encoding="utf-8-sig", errors="replace") != content:
            out_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        audit_target = workspace.translation_audit_path
        if audit != audit_target.resolve():
            shutil.copy2(audit, audit_target)
        repair_generated_json(audit_target, workspace.root_path, apply=True)

    image_issues = validate_image_links(out_path) if out_path.exists() else []
    if not args.dry_run:
        report = load_quality_report(workspace.quality_path, str(workspace.root_path))
        report.source_language = "en"
        report.source_fulltext_status = "pass"
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
