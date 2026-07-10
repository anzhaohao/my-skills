from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path


def default_cache_root() -> Path:
    configured = os.environ.get("LITERATURE_WORKFLOW_CACHE_ROOT")
    root = Path(configured).expanduser() if configured else Path(tempfile.gettempdir()) / "azf-literature-workflow"
    return root.resolve()


def workspace_cache_key(workspace_root: Path) -> str:
    resolved = workspace_root.expanduser().resolve()
    label = re.sub(r"[^0-9A-Za-z._-]+", "-", resolved.name).strip("-._") or "paper"
    digest = hashlib.sha1(str(resolved).casefold().encode("utf-8")).hexdigest()[:12]
    return f"{label[:48]}-{digest}"


def workspace_cache_root(workspace_root: Path, cache_root: Path | None = None) -> Path:
    root = (cache_root or default_cache_root()).expanduser().resolve()
    return root / workspace_cache_key(workspace_root)


def mineru_cache_dir(workspace_root: Path, cache_root: Path | None = None) -> Path:
    return workspace_cache_root(workspace_root, cache_root) / "mineru"


def figure_cache_dir(workspace_root: Path, cache_root: Path | None = None) -> Path:
    return workspace_cache_root(workspace_root, cache_root) / "figures"


def find_cached_mineru_raw(workspace_root: Path, cache_root: Path | None = None) -> Path | None:
    root = mineru_cache_dir(workspace_root, cache_root)
    if not root.exists():
        return None
    candidates = sorted(root.rglob("*_middle.json")) + sorted(root.rglob("*middle*.json"))
    return candidates[0] if candidates else None


def find_cached_mineru_auto_dir(workspace_root: Path, cache_root: Path | None = None) -> Path | None:
    root = mineru_cache_dir(workspace_root, cache_root)
    if not root.exists():
        return None
    candidates = [root, *root.rglob("auto")]
    for candidate in candidates:
        if any(candidate.glob("*.md")) and any(candidate.glob("*_middle.json")):
            return candidate
    return None


def cleanup_workspace_cache(workspace_root: Path, cache_root: Path | None = None) -> list[str]:
    cache_base = (cache_root or default_cache_root()).expanduser().resolve()
    target = workspace_cache_root(workspace_root, cache_base).resolve()
    target.relative_to(cache_base)
    removed: list[str] = []
    if target.is_dir():
        shutil.rmtree(target)
        removed.append(str(target))
    return removed


def cleanup_legacy_workspace_transients(workspace_root: Path) -> list[str]:
    root = workspace_root.expanduser().resolve()
    source = root / "附件" / "原文"
    figures = root / "附件" / "图片"
    removable_dirs = [
        root / "_figure_skill_output",
        root / "附件" / "assets",
        source / "_mineru_output",
        source / "MinerU_images",
    ]
    removable_files = [
        source / "MinerU原始输出.json",
        source / "MinerU内容列表.json",
        source / "MinerU内容列表v2.json",
    ]
    removed: list[str] = []
    for directory in removable_dirs:
        resolved = directory.resolve()
        resolved.relative_to(root)
        if resolved.is_dir():
            shutil.rmtree(resolved)
            removed.append(str(resolved))
    for file_path in removable_files:
        resolved = file_path.resolve()
        resolved.relative_to(root)
        if resolved.is_file():
            resolved.unlink()
            removed.append(str(resolved))
    if figures.is_dir():
        for pattern in ("Page-*-preview.png", "page_*.png", "*preview*.png"):
            for preview in figures.glob(pattern):
                resolved = preview.resolve()
                resolved.relative_to(root)
                if resolved.is_file():
                    resolved.unlink()
                    removed.append(str(resolved))
    return removed