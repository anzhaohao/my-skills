from __future__ import annotations

import json
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.services.workspace_paths import resolve_workspace_path


FORBIDDEN_CACHE_DIRS = (
    "_figure_skill_output",
    "附件/assets",
    "附件/原文/_mineru_output",
    "附件/原文/MinerU_images",
)


def validate_workspace_cleanliness(workspace_root: Path, *, paper: PaperWorkspace | None = None) -> list[str]:
    root = workspace_root.resolve()
    workspace = paper or PaperWorkspace.from_root(root)
    issues: list[str] = []
    for json_path in root.rglob("*.json"):
        issues.append(f"machine JSON retained in Obsidian paper workspace: {json_path}")
    if workspace.legacy_state_path.exists():
        issues.append(f"legacy state folder retained in Obsidian paper workspace: {workspace.legacy_state_path}")
    pdf_files = sorted(root.rglob("*.pdf"))
    expected_pdf = workspace.source_path / "原文.pdf"
    if pdf_files != [expected_pdf]:
        issues.append(f"paper workspace must contain only 附件/原文/原文.pdf; found {len(pdf_files)} PDF files")
    for relative in FORBIDDEN_CACHE_DIRS:
        path = root / Path(relative)
        if path.exists():
            issues.append(f"cache directory retained in vault: {path}")
    for name in ("MinerU原始输出.json", "MinerU内容列表.json", "MinerU内容列表v2.json"):
        path = root / "附件" / "原文" / name
        if path.exists():
            issues.append(f"MinerU cache file retained in vault: {path}")
    figure_dir = root / "附件" / "图片"
    if figure_dir.is_dir():
        for pattern in ("Page-*-preview.png", "page_*.png", "*preview*.png"):
            for preview in figure_dir.glob(pattern):
                issues.append(f"preview image retained in final figure folder: {preview}")
    manifest_path = workspace.figure_manifest_path
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            issues.append(f"invalid figure manifest JSON: {exc}")
        else:
            for item in manifest:
                if item.get("crop_status") != "success" or not item.get("accepted_as_highres_figure", True):
                    issues.append(f"unaccepted asset retained in final manifest: {item.get('asset_id')}")
                path = resolve_workspace_path(root, item.get("file_path", ""))
                if not path.is_file():
                    issues.append(f"manifest asset missing: {path}")
    return issues
