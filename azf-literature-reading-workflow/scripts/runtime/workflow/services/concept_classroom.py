from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig", errors="replace").lstrip("\ufeff\r\n")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def find_concept_card(concept_folder: Path, aliases: list[str]) -> Path | None:
    if not concept_folder.exists():
        return None
    lowered = {alias.casefold().strip() for alias in aliases if alias.strip()}
    for path in concept_folder.glob("*.md"):
        if path.stem.casefold() in lowered:
            return path
        metadata = _frontmatter(path)
        candidates = [metadata.get("英文名", ""), *(metadata.get("aliases") or [])]
        if any(str(candidate).casefold().strip() in lowered for candidate in candidates if str(candidate).strip()):
            return path
    return None


def ensure_concept_card(
    concept_folder: Path,
    term_en: str,
    term_zh: str,
    aliases: list[str] | None = None,
    related_papers: list[str] | None = None,
) -> Path:
    aliases = aliases or []
    related_papers = related_papers or []
    existing = find_concept_card(concept_folder, [term_en, term_zh, *aliases])
    if existing:
        return existing
    concept_folder.mkdir(parents=True, exist_ok=True)
    path = concept_folder / f"{term_zh or term_en}.md"
    now = datetime.now().isoformat(timespec="minutes")
    lines = [
        "---",
        "类型: 概念卡",
        f"英文名: {term_en}",
        "aliases:",
        *[f"  - {item}" for item in aliases],
        "领域: []",
        "主题: []",
        "概念类型:",
        "状态: 待整理",
        "相关论文:",
        *[f"  - {item}" for item in related_papers],
        f"创建时间: {now}",
        f"修改时间: {now}",
        "---",
        "",
        "# 一句话解释",
        "",
        "待补充。",
        "",
        "# 在不同论文中的用法",
        "",
        "# 相关概念",
        "",
        "# 待核对",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path