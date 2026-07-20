from __future__ import annotations

from dataclasses import asdict, dataclass


VALID_SOURCE_TYPES = {"pdf_page", "mineru_span", "figure", "table", "section", "paragraph"}
VALID_CONFIDENCE = {"high", "medium", "low", "needs_review"}


@dataclass(slots=True)
class SourceAnchor:
    anchor_id: str
    paper_workspace: str
    source_type: str
    note_target: str
    page: int | None = None
    section: str | None = None
    figure_label: str | None = None
    span_ref: str | None = None
    pdf_link: str | None = None
    path_base: str | None = None
    confidence: str = "needs_review"
    review_note: str | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.anchor_id:
            issues.append("anchor_id is required")
        if not self.paper_workspace:
            issues.append("paper_workspace is required")
        if self.source_type not in VALID_SOURCE_TYPES:
            issues.append(f"invalid source_type: {self.source_type}")
        if not self.note_target:
            issues.append("note_target is required")
        if self.confidence not in VALID_CONFIDENCE:
            issues.append(f"invalid confidence: {self.confidence}")
        if self.page is not None and self.page < 1:
            issues.append("page must be >= 1")
        return issues

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SourceAnchor":
        allowed = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in data.items() if key in allowed})

