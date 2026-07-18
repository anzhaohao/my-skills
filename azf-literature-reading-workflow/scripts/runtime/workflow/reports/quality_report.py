from __future__ import annotations

import json
from pathlib import Path

from workflow.models.quality_report import PaperQualityReport


def load_quality_report(path: Path, paper_workspace: str) -> PaperQualityReport:
    if path.exists():
        return PaperQualityReport.from_dict(json.loads(path.read_text(encoding="utf-8-sig")))
    return PaperQualityReport(paper_workspace=paper_workspace)


def public_report_dict(report: PaperQualityReport) -> dict:
    data = report.to_dict()
    data.pop("updated_at", None)
    return data


def save_quality_report(path: Path, report: PaperQualityReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    report.paper_workspace = "."
    report.recompute_overall()
    data = public_report_dict(report)
    data["path_base"] = "paper_workspace"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
