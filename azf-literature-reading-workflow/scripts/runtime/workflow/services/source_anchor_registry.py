from __future__ import annotations

import json
from pathlib import Path

from workflow.models.source_anchor import SourceAnchor


class SourceAnchorRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.anchors: list[SourceAnchor] = []
        if path.exists():
            self.load()

    def load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.anchors = [SourceAnchor.from_dict(item) for item in data]

    def add(self, anchor: SourceAnchor) -> None:
        existing = {item.anchor_id: index for index, item in enumerate(self.anchors)}
        if anchor.anchor_id in existing:
            self.anchors[existing[anchor.anchor_id]] = anchor
        else:
            self.anchors.append(anchor)

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([anchor.to_dict() for anchor in self.anchors], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.path

    def issues(self) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()
        for anchor in self.anchors:
            if anchor.anchor_id in seen:
                output.append(f"duplicate anchor_id: {anchor.anchor_id}")
            seen.add(anchor.anchor_id)
            output.extend(anchor.validate())
        return output

