from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace


FORBIDDEN_CACHE_DIRS = (
    "_figure_skill_output",
    "附件/assets",
    "附件/原文/_mineru_output",
    "附件/原文/MinerU_images",
)


def validate_workspace_cleanliness(workspace_root: Path) -> list[str]:
    root = workspace_root.resolve()
    workspace = PaperWorkspace.from_root(root)
    issues: list[str] = []
    for relative in FORBIDDEN_CACHE_DIRS:
        path = root / Path(relative)
        if path.exists():
            issues.append(f"cache directory retained in vault: {path}")
    for name in ("MinerU原始输出.json", "MinerU内容列表.json", "MinerU内容列表v2.json"):
        path = root / "附件" / "原文" / name
        if path.exists():
            issues.append(f"MinerU cache file retained in vault: {path}")
    state_dir = root / "附件" / "状态"
    if state_dir.exists():
        retained = sorted(path for path in state_dir.rglob("*") if path.is_file())
        if retained:
            issues.extend(f"machine state JSON must live under external artifact_root: {path}" for path in retained)
        else:
            issues.append(f"empty legacy state directory retained in vault: {state_dir}")
    figure_dir = root / "附件" / "图片"
    if figure_dir.is_dir():
        for pattern in ("Page-*-preview.png", "page_*.png", "*preview*.png"):
            for preview in figure_dir.glob(pattern):
                issues.append(f"preview image retained in final figure folder: {preview}")
    return issues
