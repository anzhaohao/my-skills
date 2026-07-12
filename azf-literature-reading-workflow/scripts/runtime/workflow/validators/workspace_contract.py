from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace


def _frontmatter(text: str) -> str:
    return text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""


def _has_property(frontmatter: str, key: str) -> bool:
    return any(line.startswith(f"{key}:") for line in frontmatter.splitlines())


def validate_workspace_contract(workspace_root: Path) -> list[str]:
    workspace = PaperWorkspace.from_root(workspace_root)
    issues: list[str] = []
    required_dirs = [
        workspace.reading_workspace_path,
        workspace.attachment_path,
        workspace.source_path,
        workspace.figure_path,
        workspace.state_path,
    ]
    required_files = [
        workspace.overview_note,
        workspace.source_path / "原文.pdf",
    ]
    for folder in required_dirs:
        if not folder.is_dir():
            issues.append(f"missing folder: {folder}")
    for file_path in required_files:
        if not file_path.is_file():
            issues.append(f"missing file: {file_path}")
    if workspace.overview_note.exists():
        text = workspace.overview_note.read_text(encoding="utf-8", errors="replace")
        frontmatter = _frontmatter(text)
        if "笔记类型: 索引" not in frontmatter:
            issues.append("overview 笔记类型 must be 索引")
        if "论文笔记类型: 论文总览" not in frontmatter:
            issues.append("overview 论文笔记类型 must be 论文总览")
        if "笔记状态:" not in frontmatter:
            issues.append("overview missing 笔记状态")
        if _has_property(frontmatter, "类型"):
            issues.append("overview must not contain legacy 类型 property")
        for marker in ["## 导航", "## 下一步"]:
            if marker not in text:
                issues.append(f"overview missing marker: {marker}")
        if _has_property(frontmatter, "工作区"):
            issues.append("overview must not contain 工作区 property")
        if _has_property(frontmatter, "处理状态"):
            issues.append("overview must not contain nested 处理状态 property")
        if '原文PDF: "[[' not in frontmatter:
            issues.append("overview 原文PDF property must be an Obsidian wikilink")
        if 'MinerU英文全文: "[[' not in frontmatter:
            issues.append("overview MinerU英文全文 property must be an Obsidian wikilink")
    return issues


def workspace_status(workspace_root: Path) -> str:
    return "pass" if not validate_workspace_contract(workspace_root) else "fail"
