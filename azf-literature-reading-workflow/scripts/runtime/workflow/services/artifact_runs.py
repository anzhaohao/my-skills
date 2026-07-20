from __future__ import annotations

import json
from pathlib import Path


def _workspace_key(workspace: Path) -> str:
    return f"workspace:{workspace.name.lower()}"


def latest_successful_state_dir(artifact_root: Path | str | None, workspace: Path) -> Path | None:
    if not artifact_root:
        return None
    root = Path(artifact_root).expanduser().resolve()
    index_path = root / "index.json"
    if not index_path.is_file():
        return None
    try:
        index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    papers = index.get("papers") if isinstance(index, dict) else None
    if not isinstance(papers, dict):
        return None
    paper_key = None
    lookup = index.get("lookup")
    if isinstance(lookup, dict):
        paper_key = lookup.get(_workspace_key(workspace.resolve())) or lookup.get(_workspace_key(workspace))
    if not paper_key:
        workspace_resolved = str(workspace.resolve()).lower()
        for key, item in papers.items():
            if not isinstance(item, dict):
                continue
            candidates = [str(item.get("paper_workspace", "")).lower(), str(item.get("paper_workspace_relative", "")).lower()]
            if workspace_resolved in candidates or workspace.name.lower() in candidates:
                paper_key = key
                break
    if not paper_key or paper_key not in papers:
        return None
    paper = papers.get(paper_key)
    if not isinstance(paper, dict):
        return None
    run_id = paper.get("latest_successful")
    if not run_id:
        return None
    state_dir = root / str(run_id) / "state"
    return state_dir if state_dir.is_dir() else None


def state_file(state_dir: Path | None, name: str) -> Path | None:
    if not state_dir:
        return None
    path = state_dir / name
    return path if path.is_file() else None
