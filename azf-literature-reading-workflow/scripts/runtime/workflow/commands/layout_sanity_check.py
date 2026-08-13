from __future__ import annotations

import json
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import workspace_with_artifacts
from workflow.validators.layout_sanity import simple_layout_sanity


def run(args) -> int:
    locations = getattr(args, "resolved_locations", {}) or {}
    workspace = workspace_with_artifacts(Path(args.workspace), locations.get("artifact_root"), create=True)
    markdown = workspace.chinese_fulltext_path() if workspace.source_language == "zh" else workspace.mineru_source_path()
    status, notes = simple_layout_sanity(markdown)
    report = load_quality_report(workspace.quality_path, str(workspace.root_path))
    report.layout_sanity_status = status
    for note in notes:
        report.add_note(f"Layout sanity: {note}")
    if status in {"suspect", "fail"}:
        report.add_blocker("layout sanity requires manual review")
    else:
        report.blocking_issues = [issue for issue in report.blocking_issues if issue != "layout sanity requires manual review"]
    save_quality_report(workspace.quality_path, report)
    print(json.dumps({"status": status, "notes": notes}, ensure_ascii=False, indent=2))
    return 0 if status != "fail" else 2
