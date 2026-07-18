from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(slots=True)
class PaperQualityReport:
    paper_workspace: str
    source_language: str = "en"
    overall_status: str = "warning"
    metadata_status: str = "warning"
    pdf_status: str = "warning"
    mineru_status: str = "pending"
    source_fulltext_status: str = "pending"
    layout_sanity_status: str = "not_applicable"
    figure_crop_status: str = "not_applicable"
    translation_status: str = "pending"
    image_link_status: str = "warning"
    source_anchor_status: str = "warning"
    preservation_status: str = "warning"
    blocking_issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def recompute_overall(self) -> None:
        fail_values = {
            self.metadata_status,
            self.pdf_status,
            self.mineru_status,
            self.source_fulltext_status,
            self.layout_sanity_status,
            self.figure_crop_status,
            self.translation_status,
            self.image_link_status,
            self.source_anchor_status,
            self.preservation_status,
        }
        if "fail" in fail_values or self.blocking_issues:
            self.overall_status = "fail"
        elif "warning" in fail_values or "partial" in fail_values or "suspect" in fail_values or "pending" in fail_values:
            self.overall_status = "warning"
        else:
            self.overall_status = "pass"

    def add_blocker(self, issue: str) -> None:
        if issue not in self.blocking_issues:
            self.blocking_issues.append(issue)
        self.recompute_overall()

    def add_note(self, note: str) -> None:
        if note not in self.notes:
            self.notes.append(note)

    def to_dict(self) -> dict:
        data = asdict(self)
        # Keep the public schema strict by treating updated_at as extra only in internal use.
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PaperQualityReport":
        allowed = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in data.items() if key in allowed})
