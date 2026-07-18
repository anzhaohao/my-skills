from __future__ import annotations

import json
from pathlib import Path


def load_figure_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def manifest_issues(path: Path, workspace_root: Path | None = None) -> list[str]:
    issues: list[str] = []
    for index, item in enumerate(load_figure_manifest(path)):
        for key in ["asset_id", "file_path", "source_pdf", "page", "crop_status"]:
            if key not in item:
                issues.append(f"manifest item {index} missing {key}")
        if workspace_root:
            from workflow.services.workspace_paths import resolve_workspace_path
            file_path = resolve_workspace_path(workspace_root, item.get("file_path", ""))
        else:
            file_path = Path(item.get("file_path", ""))
        if item.get("file_path") and not file_path.exists():
            issues.append(f"manifest file does not exist: {file_path}")
    return issues
