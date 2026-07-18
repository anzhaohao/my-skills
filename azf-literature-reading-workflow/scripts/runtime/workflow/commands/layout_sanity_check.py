from __future__ import annotations

import json
from pathlib import Path

from workflow.reports.quality_report import load_quality_report, save_quality_report
from workflow.services.artifact_runs import resolve_run_from_args
from workflow.validators.layout_sanity import simple_layout_sanity


def run(args) -> int:
    workspace, _artifact = resolve_run_from_args(args)
    markdown = workspace.mineru_markdown_path
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
