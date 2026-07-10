from __future__ import annotations

import json
from pathlib import Path


FORBIDDEN_CACHE_DIRS = (
    "_figure_skill_output",
    "附件/assets",
    "附件/原文/_mineru_output",
    "附件/原文/MinerU_images",
)


def validate_workspace_cleanliness(workspace_root: Path) -> list[str]:
    root = workspace_root.resolve()
    issues: list[str] = []
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
    manifest_path = root / "figure_extraction_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            issues.append(f"invalid figure manifest JSON: {exc}")
        else:
            for item in manifest:
                if item.get("crop_status") != "success" or not item.get("accepted_as_highres_figure", True):
                    issues.append(f"unaccepted asset retained in final manifest: {item.get('asset_id')}")
                path = Path(item.get("file_path", ""))
                if not path.is_file():
                    issues.append(f"manifest asset missing: {path}")
    return issues