from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow.models.artifact import ArtifactRun
from workflow.models.paper import PaperWorkspace
from workflow.services.zotero_links import extract_frontmatter_value


ARTIFACT_ID_PATTERN = re.compile(r"^\d{8}_\d{6}__[a-z0-9._-]+$")
WINDOWS_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def doi_slug(doi: str | None, zotero_key: str | None = None) -> str:
    normalized = (doi or "").strip().casefold()
    if normalized:
        normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", normalized)
        value = WINDOWS_ILLEGAL.sub("_", normalized)
        value = re.sub(r"\s+", "_", value).strip(" ._")
        return value or "no-doi__unknown"
    key = WINDOWS_ILLEGAL.sub("_", (zotero_key or "unknown").strip().casefold()).strip(" ._")
    return f"no-doi__zotero-{key or 'unknown'}"


def make_artifact_id(doi: str | None, zotero_key: str | None = None, *, when: datetime | None = None) -> str:
    stamp = (when or datetime.now().astimezone()).strftime("%Y%m%d_%H%M%S")
    return f"{stamp}__{doi_slug(doi, zotero_key)}"


def _atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_index(artifact_root: Path) -> dict[str, Any]:
    path = artifact_root / "index.json"
    if not path.is_file():
        return {"schema_version": 1, "updated_at": None, "papers": {}, "lookup": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid artifact index: {path}")
    data.setdefault("schema_version", 1)
    data.setdefault("papers", {})
    data.setdefault("lookup", {})
    return data


def save_index(artifact_root: Path, data: dict[str, Any]) -> Path:
    data["schema_version"] = 1
    data["updated_at"] = now_iso()
    path = artifact_root / "index.json"
    _atomic_json(path, data)
    return path


def overview_identity(workspace: PaperWorkspace) -> dict[str, str]:
    if not workspace.overview_note.is_file():
        return {"doi": "", "zotero_key": "", "artifact_id": ""}
    text = workspace.overview_note.read_text(encoding="utf-8-sig", errors="replace")
    return {
        "doi": extract_frontmatter_value(text, "DOI"),
        "zotero_key": extract_frontmatter_value(text, "Zotero条目键"),
        "artifact_id": extract_frontmatter_value(text, "外部产物ID"),
    }


def paper_id(doi: str | None, zotero_key: str | None, workspace: Path) -> str:
    if (doi or "").strip():
        return f"doi:{doi_slug(doi)}"
    if (zotero_key or "").strip():
        return f"zotero:{zotero_key.strip().casefold()}"
    return f"workspace:{workspace.name.casefold()}"


def _workspace_relative(workspace: Path, paper_root: Path | None) -> str | None:
    if paper_root is None:
        return None
    try:
        return workspace.resolve().relative_to(paper_root.resolve()).as_posix()
    except ValueError:
        return None


def initialize_run(
    artifact_root: Path,
    workspace: Path,
    *,
    artifact_id: str,
    doi: str | None,
    zotero_key: str | None,
    paper_root: Path | None = None,
    created_at: str | None = None,
    status: str = "attempt",
) -> ArtifactRun:
    if not ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
        raise ValueError(f"invalid artifact id: {artifact_id}")
    root = artifact_root.resolve() / artifact_id
    run = ArtifactRun(artifact_id=artifact_id, root_path=root, paper_workspace=workspace.resolve())
    for folder in [run.root_path, run.state_path, run.parser_path, run.logs_path]:
        folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "artifact_id": artifact_id,
        "status": status,
        "created_at": created_at or now_iso(),
        "completed_at": None,
        "doi": (doi or "").strip(),
        "zotero_key": (zotero_key or "").strip(),
        "paper_workspace": str(workspace.resolve()),
        "paper_workspace_relative": _workspace_relative(workspace, paper_root),
        "path_base": "paper_workspace",
    }
    if run.manifest_path.is_file():
        existing = json.loads(run.manifest_path.read_text(encoding="utf-8-sig"))
        if existing.get("artifact_id") != artifact_id:
            raise RuntimeError(f"artifact manifest id mismatch: {run.manifest_path}")
        manifest = existing
    else:
        _atomic_json(run.manifest_path, manifest)

    index = load_index(artifact_root)
    pid = paper_id(doi, zotero_key, workspace)
    entry = index["papers"].setdefault(pid, {
        "doi": (doi or "").strip(),
        "zotero_keys": [],
        "paper_workspace": str(workspace.resolve()),
        "paper_workspace_relative": _workspace_relative(workspace, paper_root),
        "latest_attempt": None,
        "latest_successful": None,
    })
    if zotero_key and zotero_key not in entry["zotero_keys"]:
        entry["zotero_keys"].append(zotero_key)
    entry["paper_workspace"] = str(workspace.resolve())
    entry["paper_workspace_relative"] = _workspace_relative(workspace, paper_root)
    entry["latest_attempt"] = artifact_id
    if doi:
        index["lookup"][f"doi:{doi_slug(doi)}"] = pid
    if zotero_key:
        index["lookup"][f"zotero:{zotero_key.casefold()}"] = pid
    index["lookup"][f"workspace:{workspace.name.casefold()}"] = pid
    save_index(artifact_root, index)
    return run


def _find_index_entry(index: dict[str, Any], workspace: Path, doi: str, zotero_key: str) -> dict[str, Any] | None:
    keys = []
    if doi:
        keys.append(f"doi:{doi_slug(doi)}")
    if zotero_key:
        keys.append(f"zotero:{zotero_key.casefold()}")
    keys.append(f"workspace:{workspace.name.casefold()}")
    for key in keys:
        pid = index.get("lookup", {}).get(key)
        if pid and pid in index.get("papers", {}):
            return index["papers"][pid]
    return None


def resolve_run(
    artifact_root: Path,
    workspace_root: Path,
    *,
    artifact_id: str | None = None,
    create_if_missing: bool = False,
    paper_root: Path | None = None,
) -> tuple[PaperWorkspace, ArtifactRun]:
    base_workspace = PaperWorkspace.from_root(workspace_root)
    identity = overview_identity(base_workspace)
    selected = (artifact_id or identity["artifact_id"]).strip()
    index = load_index(artifact_root)
    entry = _find_index_entry(index, base_workspace.root_path, identity["doi"], identity["zotero_key"])
    if not selected and entry:
        selected = entry.get("latest_successful") or ""
    if not selected and create_if_missing:
        selected = make_artifact_id(identity["doi"], identity["zotero_key"])
    if not selected:
        raise RuntimeError(f"no successful external artifact is registered for workspace: {base_workspace.root_path}")
    run_root = artifact_root.resolve() / selected
    if not run_root.is_dir():
        if not create_if_missing:
            raise RuntimeError(f"external artifact run is missing: {run_root}")
        run = initialize_run(
            artifact_root,
            base_workspace.root_path,
            artifact_id=selected,
            doi=identity["doi"],
            zotero_key=identity["zotero_key"],
            paper_root=paper_root,
        )
    else:
        run = ArtifactRun(selected, run_root, base_workspace.root_path)
    workspace = PaperWorkspace.from_root(
        base_workspace.root_path,
        state_path_override=run.state_path,
        artifact_id=run.artifact_id,
    )
    return workspace, run


def resolve_run_from_args(
    args,
    *,
    workspace: str | Path | None = None,
    create_if_missing: bool = True,
    require_writable: bool = True,
) -> tuple[PaperWorkspace, ArtifactRun]:
    locations = getattr(args, "resolved_locations", {})
    artifact_root = locations.get("artifact_root")
    if artifact_root is None:
        raise RuntimeError("confirmed artifact_root is required")
    paper_root = locations.get("paper_root")
    workspace_root = Path(workspace or args.workspace)
    paper, run = resolve_run(
        artifact_root,
        workspace_root,
        artifact_id=getattr(args, "artifact_id", None),
        create_if_missing=create_if_missing,
        paper_root=paper_root,
    )
    if require_writable and run.manifest_path.is_file():
        manifest = json.loads(run.manifest_path.read_text(encoding="utf-8-sig"))
        if manifest.get("status") == "success":
            raise RuntimeError(
                f"artifact run is already successful and immutable: {run.artifact_id}; "
                "start a new run with an explicit --artifact-id"
            )
    return paper, run


def promote_run(artifact_root: Path, run: ArtifactRun, *, quality_status: str, completed_at: str | None = None) -> None:
    if quality_status != "pass":
        raise RuntimeError("only a fully passing artifact run can be promoted")
    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8-sig"))
    finished = completed_at or now_iso()
    manifest["status"] = "success"
    manifest["completed_at"] = finished
    _atomic_json(run.manifest_path, manifest)
    index = load_index(artifact_root)
    identity = overview_identity(PaperWorkspace.from_root(run.paper_workspace))
    entry = _find_index_entry(index, run.paper_workspace, identity["doi"], identity["zotero_key"])
    if entry is None:
        raise RuntimeError(f"artifact index entry missing for {run.paper_workspace}")
    entry["latest_attempt"] = run.artifact_id
    entry["latest_successful"] = run.artifact_id
    save_index(artifact_root, index)


def mark_run_failed(artifact_root: Path, run: ArtifactRun, reason: str) -> None:
    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("status") == "success":
        manifest["last_revalidation_failure"] = {"checked_at": now_iso(), "reason": reason}
        _atomic_json(run.manifest_path, manifest)
        return
    manifest["status"] = "failed"
    manifest["completed_at"] = now_iso()
    manifest["failure_reason"] = reason
    _atomic_json(run.manifest_path, manifest)
    index = load_index(artifact_root)
    identity = overview_identity(PaperWorkspace.from_root(run.paper_workspace))
    entry = _find_index_entry(index, run.paper_workspace, identity["doi"], identity["zotero_key"])
    if entry is not None:
        entry["latest_attempt"] = run.artifact_id
        save_index(artifact_root, index)


def repair_run_binding(artifact_root: Path, run: ArtifactRun, paper_root: Path, *, apply: bool) -> dict[str, Any]:
    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8-sig"))
    expected_workspace = str(run.paper_workspace.resolve())
    expected_relative = _workspace_relative(run.paper_workspace, paper_root)
    changed = int(manifest.get("paper_workspace") != expected_workspace) + int(
        manifest.get("paper_workspace_relative") != expected_relative
    )
    if apply and changed:
        manifest["paper_workspace"] = expected_workspace
        manifest["paper_workspace_relative"] = expected_relative
        _atomic_json(run.manifest_path, manifest)

        index = load_index(artifact_root)
        identity = overview_identity(PaperWorkspace.from_root(run.paper_workspace))
        entry = _find_index_entry(index, run.paper_workspace, identity["doi"], identity["zotero_key"])
        if entry is not None:
            entry["paper_workspace"] = expected_workspace
            entry["paper_workspace_relative"] = expected_relative
            index["lookup"][f"workspace:{run.paper_workspace.name.casefold()}"] = paper_id(
                identity["doi"], identity["zotero_key"], run.paper_workspace
            )
            save_index(artifact_root, index)
    return {"file": str(run.manifest_path), "changed_paths": changed, "applied": bool(apply and changed)}
