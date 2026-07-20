from __future__ import annotations

import json
from pathlib import Path

from workflow.services.cache_paths import cleanup_legacy_workspace_transients, cleanup_workspace_cache
from workflow.models.paper import PaperWorkspace
from workflow.services.artifact_runs import latest_successful_state_dir, state_file
from workflow.validators.source_anchors import validate_source_anchor_file
from workflow.validators.workspace_cleanliness import validate_workspace_cleanliness
from workflow.validators.workspace_contract import validate_workspace_contract
from workflow.validators.translation_fidelity import validate_workspace_translation
from workflow.validators.translation_footnotes import validate_translation_footnotes


def run(args) -> int:
    workspaces = [Path(item).resolve() for item in args.workspaces]
    results = []
    overall_pass = True
    for workspace in workspaces:
        issues = []
        cleanup_removed: list[str] = []
        paper = PaperWorkspace.from_root(workspace)
        locations = getattr(args, "resolved_locations", {}) or {}
        external_state = latest_successful_state_dir(locations.get("artifact_root"), workspace)
        source_anchor = paper.source_anchor_path if paper.source_anchor_path.is_file() else state_file(external_state, "source-anchors.json") or paper.source_anchor_path
        translation_audit = paper.translation_audit_path if paper.translation_audit_path.is_file() else state_file(external_state, "translation-audit.json") or paper.translation_audit_path
        quality = paper.quality_path if paper.quality_path.is_file() else state_file(external_state, "quality-report.json") or paper.quality_path
        quality_data = None
        if quality.exists():
            quality_data = json.loads(quality.read_text(encoding="utf-8-sig"))
        issues.extend(validate_workspace_contract(workspace))
        issues.extend(validate_source_anchor_file(source_anchor))
        issues.extend(validate_workspace_cleanliness(workspace))
        issues.extend(validate_workspace_translation(workspace, translation_audit))
        for note in sorted(paper.reading_workspace_path.glob("【中译】*.md")):
            issues.extend(validate_translation_footnotes(note))
        if not quality.exists():
            issues.append(f"missing quality report: {quality}")
        elif quality_data and quality_data.get("overall_status") != "pass":
            issues.append(f"quality report not pass: {quality_data.get('overall_status')}")
        if issues:
            overall_pass = False
        elif quality_data and quality_data.get("overall_status") == "pass" and not args.keep_cache:
            cleanup_removed.extend(cleanup_workspace_cache(workspace))
            cleanup_removed.extend(cleanup_legacy_workspace_transients(workspace))
        results.append(
            {
                "workspace": str(workspace),
                "issues": issues,
                "cleanup_removed": cleanup_removed,
                "status": "pass" if not issues else "fail",
            }
        )
    output = {"overall_status": "pass" if overall_pass else "fail", "workspaces": results}
    if getattr(args, "output", None):
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if overall_pass else 2