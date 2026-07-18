from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PATH_KEYS = {
    "paper_workspace",
    "workspace",
    "project_dir",
    "file_path",
    "source_pdf",
    "pdf_path",
    "pdf",
    "mineru_markdown",
    "chinese_note",
    "deep_reading_note",
    "translation_file",
    "translation_note",
    "translation_audit",
    "mineru_fulltext",
    "chinese_source_note",
    "source_image",
    "regions_file",
    "crops_dir",
    "mineru_images_dir",
    "mineru_pdf_folder",
}
WORKSPACE_MARKERS = ("附件", "阅读工作台")


def _is_external_reference(value: str) -> bool:
    lowered = value.casefold()
    return lowered.startswith(("http://", "https://", "zotero://"))


def relocate_legacy_workspace_path(workspace_root: Path, value: str) -> Path | None:
    root = workspace_root.resolve()
    if value in {"", "."}:
        return root
    path = Path(value)
    if not path.is_absolute():
        return root / path
    if path.exists():
        return path
    if path.name == root.name:
        return root
    parts = list(path.parts)
    for marker in WORKSPACE_MARKERS:
        if marker not in parts:
            continue
        candidate = root.joinpath(*parts[parts.index(marker) :])
        if candidate.exists():
            return candidate
    return None


def resolve_workspace_path(workspace_root: Path, value: str) -> Path:
    relocated = relocate_legacy_workspace_path(workspace_root, value)
    if relocated is not None:
        return relocated.resolve()
    path = Path(value)
    return path.resolve() if path.is_absolute() else (workspace_root / path).resolve()


def workspace_relative_value(workspace_root: Path, value: str) -> str:
    if not value or _is_external_reference(value):
        return value
    root = workspace_root.resolve()
    relocated = relocate_legacy_workspace_path(root, value)
    if relocated is None:
        return value
    try:
        relative = relocated.resolve().relative_to(root)
    except ValueError:
        return value
    return "." if not relative.parts else relative.as_posix()


def normalize_generated_paths(data: Any, workspace_root: Path, *, parent_key: str | None = None) -> tuple[Any, int]:
    if isinstance(data, dict):
        changed = 0
        output: dict[str, Any] = {}
        contains_workspace_path = any(key in PATH_KEYS for key in data)
        for key, value in data.items():
            normalized, count = normalize_generated_paths(value, workspace_root, parent_key=key)
            output[key] = normalized
            changed += count
        if contains_workspace_path and output.get("path_base") != "paper_workspace":
            output["path_base"] = "paper_workspace"
            changed += 1
        return output, changed
    if isinstance(data, list):
        changed = 0
        output = []
        for value in data:
            normalized, count = normalize_generated_paths(value, workspace_root, parent_key=parent_key)
            output.append(normalized)
            changed += count
        return output, changed
    if isinstance(data, str) and parent_key in PATH_KEYS:
        normalized = workspace_relative_value(workspace_root, data)
        return normalized, int(normalized != data)
    return data, 0


def repair_generated_json(path: Path, workspace_root: Path, *, apply: bool) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    normalized, changed = normalize_generated_paths(data, workspace_root)
    if apply and changed:
        path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"file": str(path), "changed_paths": changed, "applied": bool(apply and changed)}


def validate_generated_json_paths(path: Path, workspace_root: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    issues: list[str] = []
    required_targets = {
        "file_path",
        "source_pdf",
        "pdf_path",
        "pdf",
        "mineru_markdown",
        "chinese_note",
        "deep_reading_note",
        "translation_file",
    }

    def walk(value: Any, parent_key: str | None = None) -> None:
        if isinstance(value, dict):
            if any(key in PATH_KEYS for key in value) and value.get("path_base") != "paper_workspace":
                issues.append(f"missing path_base=paper_workspace in {path}")
            for key, child in value.items():
                walk(child, key)
        elif isinstance(value, list):
            for child in value:
                walk(child, parent_key)
        elif isinstance(value, str) and parent_key in required_targets and value and not _is_external_reference(value):
            candidate = resolve_workspace_path(workspace_root, value.split("#", 1)[0])
            if not candidate.exists():
                issues.append(f"external state target missing: {candidate} ({path.name}:{parent_key})")

    walk(data)
    return issues
