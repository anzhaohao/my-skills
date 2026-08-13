from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from workflow.models.paper import PaperSource, PaperWorkspace


def _workspace_key(workspace: Path) -> str:
    return f"workspace:{workspace.name.lower()}"


def _read_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _frontmatter_value(note: Path, key: str) -> str:
    if not note.is_file():
        return ""
    text = note.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---") or text.count("---") < 2:
        return ""
    for line in text.split("---", 2)[1].splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _empty_index() -> dict:
    return {
        "schema_version": 1,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "papers": {},
        "lookup": {},
    }


def _load_index(root: Path) -> dict:
    index = _read_json(root / "index.json", _empty_index())
    if not isinstance(index, dict):
        index = _empty_index()
    index.setdefault("schema_version", 1)
    index.setdefault("papers", {})
    index.setdefault("lookup", {})
    return index


def _save_index(root: Path, index: dict) -> None:
    index["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_json(root / "index.json", index)


def _find_paper_key(index: dict, workspace: Path) -> str | None:
    lookup = index.get("lookup") if isinstance(index, dict) else None
    if isinstance(lookup, dict):
        found = lookup.get(_workspace_key(workspace.resolve())) or lookup.get(_workspace_key(workspace))
        if found:
            return str(found)
    workspace_resolved = str(workspace.resolve()).casefold()
    papers = index.get("papers") if isinstance(index, dict) else None
    if not isinstance(papers, dict):
        return None
    for key, item in papers.items():
        if not isinstance(item, dict):
            continue
        candidates = {
            str(item.get("paper_workspace", "")).casefold(),
            str(item.get("paper_workspace_relative", "")).casefold(),
        }
        if workspace_resolved in candidates or workspace.name.casefold() in candidates:
            return str(key)
    return None


def _identity(source: PaperSource | None, workspace: Path) -> tuple[str, str]:
    if source and source.doi:
        doi_slug = re.sub(r"[^0-9a-z.-]+", "_", source.doi.casefold()).strip("_.")
        return f"doi:{doi_slug}", doi_slug
    if source and source.zotero_key:
        zotero = source.zotero_key.casefold()
        return f"zotero:{zotero}", zotero
    slug = re.sub(r"[^0-9a-z\u4e00-\u9fff.-]+", "-", workspace.name.casefold()).strip("-.")
    return _workspace_key(workspace), slug[:72] or "paper"


def resolve_artifact_id(artifact_root: Path | str | None, workspace: Path) -> str | None:
    if not artifact_root:
        return None
    root = Path(artifact_root).expanduser().resolve()
    paper = PaperWorkspace.from_root(workspace)
    from_overview = _frontmatter_value(paper.overview_note, "外部产物ID")
    if from_overview and (root / from_overview).is_dir():
        return from_overview
    index = _load_index(root)
    paper_key = _find_paper_key(index, workspace)
    item = index.get("papers", {}).get(paper_key, {}) if paper_key else {}
    if isinstance(item, dict):
        for field in ("latest_attempt", "latest_successful"):
            artifact_id = item.get(field)
            if artifact_id and (root / str(artifact_id)).is_dir():
                return str(artifact_id)
    return None


def ensure_artifact_run(
    artifact_root: Path | str,
    workspace: Path,
    *,
    source: PaperSource | None = None,
    new_run: bool = False,
) -> tuple[str, Path]:
    root = Path(artifact_root).expanduser().resolve()
    workspace = workspace.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not new_run:
        existing = resolve_artifact_id(root, workspace)
        if existing:
            state = root / existing / "state"
            state.mkdir(parents=True, exist_ok=True)
            (root / existing / "parser").mkdir(parents=True, exist_ok=True)
            (root / existing / "logs").mkdir(parents=True, exist_ok=True)
            return existing, state

    index = _load_index(root)
    identity_key, slug = _identity(source, workspace)
    paper_key = _find_paper_key(index, workspace) or identity_key
    existing_item = index.get("papers", {}).get(paper_key, {})
    if isinstance(existing_item, dict) and existing_item.get("doi"):
        slug = re.sub(r"[^0-9a-z.-]+", "_", str(existing_item["doi"]).casefold()).strip("_.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_id = f"{stamp}__{slug}"
    suffix = 2
    while (root / artifact_id).exists():
        artifact_id = f"{stamp}__{slug}__{suffix}"
        suffix += 1
    run_root = root / artifact_id
    state = run_root / "state"
    state.mkdir(parents=True, exist_ok=False)
    (run_root / "parser").mkdir()
    (run_root / "logs").mkdir()
    manifest = {
        "schema_version": 1,
        "artifact_id": artifact_id,
        "status": "in_progress",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "completed_at": None,
        "doi": source.doi if source else None,
        "zotero_key": source.zotero_key if source else None,
        "paper_workspace": str(workspace),
        "paper_workspace_relative": workspace.name,
        "path_base": "paper_workspace",
    }
    _write_json(run_root / "run-manifest.json", manifest)

    papers = index.setdefault("papers", {})
    item = papers.setdefault(paper_key, {})
    if source and source.doi:
        item["doi"] = source.doi
    if source and source.zotero_key:
        keys = item.setdefault("zotero_keys", [])
        if source.zotero_key not in keys:
            keys.append(source.zotero_key)
    item.update(
        {
            "paper_workspace": str(workspace),
            "paper_workspace_relative": item.get("paper_workspace_relative") or workspace.name,
            "latest_attempt": artifact_id,
        }
    )
    lookup = index.setdefault("lookup", {})
    lookup[paper_key] = paper_key
    lookup[_workspace_key(workspace)] = paper_key
    if source and source.zotero_key:
        lookup[f"zotero:{source.zotero_key.casefold()}"] = paper_key
    _save_index(root, index)
    return artifact_id, state


def workspace_with_artifacts(
    workspace: Path,
    artifact_root: Path | str | None,
    *,
    source: PaperSource | None = None,
    create: bool = False,
    new_run: bool = False,
) -> PaperWorkspace:
    workspace = workspace.expanduser().resolve()
    if not artifact_root:
        return PaperWorkspace.from_root(workspace)
    root = Path(artifact_root).expanduser().resolve()
    artifact_id = resolve_artifact_id(root, workspace)
    if create and (not artifact_id or new_run):
        artifact_id, state = ensure_artifact_run(root, workspace, source=source, new_run=new_run)
    elif artifact_id:
        state = root / artifact_id / "state"
    else:
        return PaperWorkspace.from_root(workspace, artifact_root=root)
    return PaperWorkspace.from_root(
        workspace,
        state_path=state,
        artifact_root=root,
        artifact_id=artifact_id,
    )


def finalize_artifact_run(
    artifact_root: Path | str,
    workspace: Path,
    artifact_id: str,
    *,
    status: str,
    promote: bool = False,
) -> None:
    root = Path(artifact_root).expanduser().resolve()
    run_root = root / artifact_id
    manifest_path = run_root / "run-manifest.json"
    manifest = _read_json(manifest_path, {})
    manifest["status"] = status
    manifest["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_json(manifest_path, manifest)
    index = _load_index(root)
    paper_key = _find_paper_key(index, workspace.expanduser().resolve())
    if paper_key:
        item = index.setdefault("papers", {}).setdefault(paper_key, {})
        item["latest_attempt"] = artifact_id
        if promote:
            item["latest_successful"] = artifact_id
        _save_index(root, index)


def promote_artifact_run(artifact_root: Path | str, workspace: Path, artifact_id: str) -> None:
    finalize_artifact_run(
        artifact_root,
        workspace,
        artifact_id,
        status="success",
        promote=True,
    )


def latest_successful_state_dir(artifact_root: Path | str | None, workspace: Path) -> Path | None:
    if not artifact_root:
        return None
    root = Path(artifact_root).expanduser().resolve()
    index = _load_index(root)
    paper_key = _find_paper_key(index, workspace.expanduser().resolve())
    paper = index.get("papers", {}).get(paper_key, {}) if paper_key else {}
    run_id = paper.get("latest_successful") if isinstance(paper, dict) else None
    state_dir = root / str(run_id) / "state" if run_id else None
    return state_dir if state_dir and state_dir.is_dir() else None


def state_file(state_dir: Path | None, name: str) -> Path | None:
    if not state_dir:
        return None
    path = state_dir / name
    return path if path.is_file() else None
