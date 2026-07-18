from __future__ import annotations

import json
from pathlib import Path

from workflow.models.source_anchor import SourceAnchor


def validate_source_anchor_file(path: Path, workspace_root: Path | None = None) -> list[str]:
    if not path.exists():
        return [f"missing source anchor file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid source anchor JSON: {exc}"]
    if not isinstance(data, list):
        return ["source anchor file must be a JSON array"]
    issues: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            issues.append(f"anchor {index} is not an object")
            continue
        try:
            anchor = SourceAnchor.from_dict(item)
        except TypeError as exc:
            issues.append(f"anchor {index} has invalid fields: {exc}")
            continue
        if anchor.anchor_id in seen:
            issues.append(f"duplicate anchor_id: {anchor.anchor_id}")
        seen.add(anchor.anchor_id)
        issues.extend(anchor.validate())
        if workspace_root is not None:
            target_value = anchor.note_target.split("#", 1)[0]
            target = workspace_root.resolve() / Path(target_value)
            if not target.is_file():
                issues.append(f"anchor target missing in paper workspace: {target}")
    return issues
