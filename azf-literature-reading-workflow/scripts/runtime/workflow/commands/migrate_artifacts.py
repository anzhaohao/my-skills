from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow.models.paper import PaperWorkspace
from workflow.services.artifact_runs import initialize_run, make_artifact_id, mark_run_failed, promote_run
from workflow.services.overview_status import update_overview_artifact_status
from workflow.services.workspace_paths import normalize_generated_paths, validate_generated_json_paths
from workflow.services.zotero_links import extract_frontmatter_value
from workflow.validators.source_anchors import validate_source_anchor_file
from workflow.validators.translation_fidelity import validate_workspace_translation
from workflow.validators.workspace_cleanliness import validate_workspace_cleanliness
from workflow.validators.workspace_contract import validate_workspace_contract


ANCHOR_REFERENCE = re.compile(r"`?source-anchors\.json#([A-Za-z0-9._-]+)`?")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(workspace: PaperWorkspace) -> tuple[str, str]:
    text = workspace.overview_note.read_text(encoding="utf-8-sig", errors="replace")
    return extract_frontmatter_value(text, "DOI"), extract_frontmatter_value(text, "Zotero条目键")


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _explicit_times(value: Any) -> list[datetime]:
    output: list[datetime] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"verified_at", "reaudited_at"} and isinstance(child, str):
                parsed = _parse_time(child)
                if parsed:
                    output.append(parsed)
            output.extend(_explicit_times(child))
    elif isinstance(value, list):
        for child in value:
            output.extend(_explicit_times(child))
    return output


def _legacy_accepted_at(state_path: Path) -> datetime:
    quality = state_path / "quality-report.json"
    candidates = [datetime.fromtimestamp(quality.stat().st_mtime).astimezone()] if quality.is_file() else []
    for path in state_path.glob("*.json"):
        try:
            candidates.extend(_explicit_times(json.loads(path.read_text(encoding="utf-8-sig"))))
        except (OSError, json.JSONDecodeError):
            continue
    if not candidates:
        candidates.append(datetime.now().astimezone())
    aware = [item if item.tzinfo else item.astimezone() for item in candidates]
    return max(aware, key=lambda item: item.timestamp())


def _duplicate_pdfs(workspace: PaperWorkspace) -> tuple[list[Path], list[str]]:
    canonical = workspace.source_path / "原文.pdf"
    issues: list[str] = []
    duplicates: list[Path] = []
    if not canonical.is_file():
        return [], [f"canonical source PDF missing: {canonical}"]
    canonical_hash = _sha256(canonical)
    for path in sorted(workspace.root_path.rglob("*.pdf")):
        if path == canonical:
            continue
        if _sha256(path) != canonical_hash:
            issues.append(f"non-identical extra PDF requires manual review: {path}")
        else:
            duplicates.append(path)
    return duplicates, issues


def _replace_pdf_paths(value: Any, workspace: PaperWorkspace, duplicate_paths: list[Path], parent_key: str | None = None) -> tuple[Any, int]:
    duplicate_values = {str(path.resolve()).casefold() for path in duplicate_paths}
    duplicate_values.update(path.relative_to(workspace.root_path).as_posix().casefold() for path in duplicate_paths)
    if isinstance(value, dict):
        output = {}
        changed = 0
        for key, child in value.items():
            normalized, count = _replace_pdf_paths(child, workspace, duplicate_paths, key)
            output[key] = normalized
            changed += count
        return output, changed
    if isinstance(value, list):
        output = []
        changed = 0
        for child in value:
            normalized, count = _replace_pdf_paths(child, workspace, duplicate_paths, parent_key)
            output.append(normalized)
            changed += count
        return output, changed
    if isinstance(value, str) and parent_key in {"source_pdf", "pdf", "pdf_path"}:
        comparable = value.replace("\\", "/").casefold()
        absolute = str((workspace.root_path / Path(value)).resolve()).casefold() if not Path(value).is_absolute() else str(Path(value).resolve()).casefold()
        if comparable in duplicate_values or absolute in duplicate_values:
            return "附件/原文/原文.pdf", int(value != "附件/原文/原文.pdf")
    return value, 0


def _copy_and_normalize_state(workspace: PaperWorkspace, target_state: Path, duplicates: list[Path]) -> list[dict[str, Any]]:
    results = []
    target_state.mkdir(parents=True, exist_ok=True)
    for source in sorted(workspace.legacy_state_path.glob("*.json")):
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        data, pdf_changes = _replace_pdf_paths(data, workspace, duplicates)
        data, path_changes = normalize_generated_paths(data, workspace.root_path)
        target = target_state / source.name
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append({"source": str(source), "target": str(target), "changed_paths": pdf_changes + path_changes})
    return results


def _external_issues(workspace: PaperWorkspace) -> list[str]:
    issues: list[str] = []
    quality = workspace.quality_path
    quality_data = None
    if not quality.is_file():
        issues.append(f"missing quality report: {quality}")
    else:
        quality_data = json.loads(quality.read_text(encoding="utf-8-sig"))
        if quality_data.get("overall_status") != "pass":
            issues.append(f"quality report not pass: {quality_data.get('overall_status')}")
    issues.extend(validate_source_anchor_file(workspace.source_anchor_path, workspace.root_path))
    issues.extend(validate_workspace_translation(workspace.root_path, paper=workspace))
    for path in sorted(workspace.state_path.glob("*.json")):
        issues.extend(validate_generated_json_paths(path, workspace.root_path))
    return issues


def _backup_file(path: Path, workspace: PaperWorkspace, backup_root: Path, artifact_id: str) -> None:
    relative = path.relative_to(workspace.root_path)
    target = backup_root / "migrate-artifacts" / artifact_id / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def _humanize_figure_anchors(note: Path, anchor_path: Path) -> bool:
    if not note.is_file() or not anchor_path.is_file():
        return False
    anchors = json.loads(anchor_path.read_text(encoding="utf-8-sig"))
    mapping = {item.get("anchor_id"): item for item in anchors if isinstance(item, dict)}
    text = note.read_text(encoding="utf-8-sig", errors="replace")

    def replacement(match: re.Match[str]) -> str:
        item = mapping.get(match.group(1), {})
        label = item.get("figure_label") or item.get("section") or "原文位置"
        page = item.get("page")
        return f"{label}（PDF 第 {page} 页）" if page else str(label)

    updated = ANCHOR_REFERENCE.sub(replacement, text).replace("**来源锚点**", "**来源**")
    if updated == text:
        return False
    note.write_text(updated, encoding="utf-8")
    return True


def _plan_workspace(workspace_root: Path) -> dict[str, Any]:
    workspace = PaperWorkspace.from_root(workspace_root)
    doi, zotero_key = _identity(workspace)
    accepted = _legacy_accepted_at(workspace.legacy_state_path)
    artifact_id = make_artifact_id(doi, zotero_key, when=accepted)
    duplicates, issues = _duplicate_pdfs(workspace)
    json_files = sorted(workspace.legacy_state_path.glob("*.json"))
    return {
        "workspace": str(workspace.root_path),
        "doi": doi,
        "zotero_key": zotero_key,
        "artifact_id": artifact_id,
        "accepted_at": accepted.isoformat(timespec="seconds"),
        "json_files": [str(path) for path in json_files],
        "duplicate_pdfs": [str(path) for path in duplicates],
        "issues": issues + ([] if json_files else [f"no legacy state JSON found: {workspace.legacy_state_path}"]),
    }


def run(args) -> int:
    artifact_root = args.resolved_locations["artifact_root"]
    plans = [_plan_workspace(Path(value).resolve()) for value in args.workspaces]
    payload: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry-run",
        "artifact_root": str(artifact_root),
        "counts": {
            "workspaces": len(plans),
            "json_files": sum(len(item["json_files"]) for item in plans),
            "duplicate_pdfs": sum(len(item["duplicate_pdfs"]) for item in plans),
        },
        "workspaces": plans,
    }
    if not args.apply:
        payload["status"] = "fail" if any(item["issues"] for item in plans) else "pass"
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2 if payload["status"] == "fail" else 0

    if not args.backup_root:
        print(json.dumps({"status": "fail", "reason": "--backup-root is required with --apply"}, ensure_ascii=False, indent=2))
        return 2
    backup_root = Path(args.backup_root).resolve()
    vault = args.resolved_locations["vault_root"].resolve()
    try:
        backup_root.relative_to(vault)
    except ValueError:
        pass
    else:
        print(json.dumps({"status": "fail", "reason": "migration backup root must be outside the Obsidian vault"}, ensure_ascii=False, indent=2))
        return 2
    backup_root.mkdir(parents=True, exist_ok=True)

    overall_pass = True
    for item in plans:
        if item["issues"]:
            item["status"] = "fail"
            overall_pass = False
            continue
        base = PaperWorkspace.from_root(Path(item["workspace"]))
        run = initialize_run(
            artifact_root,
            base.root_path,
            artifact_id=item["artifact_id"],
            doi=item["doi"],
            zotero_key=item["zotero_key"],
            paper_root=args.resolved_locations["paper_root"],
            created_at=item["accepted_at"],
        )
        workspace = PaperWorkspace.from_root(base.root_path, state_path_override=run.state_path, artifact_id=run.artifact_id)
        duplicates = [Path(value) for value in item["duplicate_pdfs"]]
        copied = _copy_and_normalize_state(workspace, run.state_path, duplicates)
        item["copied_state"] = copied
        issues = _external_issues(workspace)
        if issues:
            item["issues"].extend(issues)
            item["status"] = "fail"
            mark_run_failed(artifact_root, run, "; ".join(issues[:10]))
            overall_pass = False
            continue

        notes_to_change = [workspace.overview_note, *workspace.reading_workspace_path.glob("【图表】*.md")]
        for path in [*workspace.legacy_state_path.glob("*.json"), *duplicates, *notes_to_change]:
            if path.is_file():
                _backup_file(path, workspace, backup_root, run.artifact_id)

        quality_data = json.loads(workspace.quality_path.read_text(encoding="utf-8-sig"))
        update_overview_artifact_status(
            workspace.overview_note,
            artifact_id=run.artifact_id,
            quality_status=quality_data.get("overall_status", "pass"),
            source_status=quality_data.get("source_anchor_status", "pass"),
            accepted_at=item["accepted_at"],
        )
        changed_figure_notes = [
            str(note) for note in workspace.reading_workspace_path.glob("【图表】*.md")
            if _humanize_figure_anchors(note, workspace.source_anchor_path)
        ]
        for path in workspace.legacy_state_path.glob("*.json"):
            path.unlink()
        if workspace.legacy_state_path.is_dir() and not any(workspace.legacy_state_path.iterdir()):
            workspace.legacy_state_path.rmdir()
        for path in duplicates:
            path.unlink()

        final_issues = []
        final_issues.extend(validate_workspace_contract(workspace.root_path, paper=workspace))
        final_issues.extend(validate_workspace_cleanliness(workspace.root_path, paper=workspace))
        final_issues.extend(_external_issues(workspace))
        if final_issues:
            item["issues"].extend(final_issues)
            item["status"] = "fail"
            mark_run_failed(artifact_root, run, "; ".join(final_issues[:10]))
            overall_pass = False
            continue
        promote_run(artifact_root, run, quality_status="pass", completed_at=item["accepted_at"])
        item["changed_figure_notes"] = changed_figure_notes
        item["status"] = "pass"

    payload["status"] = "pass" if overall_pass else "fail"
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if overall_pass else 2

