from __future__ import annotations

from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.services.wikilinks import path_qualified_wikilink_targets, wikilink_targets


def _frontmatter(text: str) -> str:
    text = text.lstrip("\ufeff")
    return text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""


def _has_property(frontmatter: str, key: str) -> bool:
    return any(line.startswith(f"{key}:") for line in frontmatter.splitlines())


def _property_value(frontmatter: str, key: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _find_vault_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def _target_matches(vault_root: Path, target: str) -> list[Path]:
    clean = target.split("#", 1)[0].strip()
    if not clean or "/" in clean or "\\" in clean:
        return []
    names = [clean] if Path(clean).suffix else [clean, f"{clean}.md"]
    matches: set[Path] = set()
    for name in names:
        matches.update(candidate.resolve() for candidate in vault_root.rglob(name) if candidate.is_file())
    return sorted(matches)


def validate_workspace_contract(workspace_root: Path) -> list[str]:
    workspace = PaperWorkspace.from_root(workspace_root)
    issues: list[str] = []
    required_dirs = [
        workspace.reading_workspace_path,
        workspace.attachment_path,
        workspace.source_path,
    ]
    required_files = [
        workspace.overview_note,
        workspace.source_pdf_path(),
        workspace.chinese_fulltext_path(),
    ]
    for folder in required_dirs:
        if not folder.is_dir():
            issues.append(f"missing folder: {folder}")
    for file_path in required_files:
        if not file_path.is_file():
            issues.append(f"missing file: {file_path}")
    if workspace.overview_note.exists():
        text = workspace.overview_note.read_text(encoding="utf-8-sig", errors="replace")
        frontmatter = _frontmatter(text)
        if not workspace.overview_note.name.startswith("【总览】"):
            issues.append("overview note filename must start with 【总览】")
        if "笔记类型: 索引" not in frontmatter:
            issues.append("overview 笔记类型 must be 索引")
        if "论文笔记类型: 论文总览" not in frontmatter:
            issues.append("overview 论文笔记类型 must be 论文总览")
        if "笔记状态:" not in frontmatter:
            issues.append("overview missing 笔记状态")
        if _has_property(frontmatter, "类型"):
            issues.append("overview must not contain legacy 类型 property")
        title_zh = ""
        for line in frontmatter.splitlines():
            if line.startswith("中文题名:"):
                title_zh = line.split(":", 1)[1].strip().strip('"')
                break
        if title_zh and f"# {title_zh}" in text:
            issues.append("overview body must not repeat the note title as an H1")
        for marker in ["# 导航", "# 下一步"]:
            if marker not in text:
                issues.append(f"overview missing marker: {marker}")
        if _has_property(frontmatter, "工作区"):
            issues.append("overview must not contain 工作区 property")
        if _has_property(frontmatter, "处理状态"):
            issues.append("overview must not contain nested 处理状态 property")
        if _has_property(frontmatter, "Zotero条目链接"):
            issues.append("overview must not contain Zotero条目链接; use Zotero PDF链接 only")
        zotero_key = _property_value(frontmatter, "Zotero条目键")
        zotero_pdf = _property_value(frontmatter, "Zotero PDF链接")
        if zotero_key and not zotero_pdf:
            issues.append("overview Zotero PDF链接 missing for Zotero-backed paper")
        if zotero_pdf and not zotero_pdf.startswith("zotero://open-pdf/library/items/"):
            issues.append("overview Zotero PDF链接 must use zotero://open-pdf/library/items/{attachment_key}")
        source_language = _property_value(frontmatter, "原文语言") or "en"
        zh_fulltext = _property_value(frontmatter, "中文全文")
        if not zh_fulltext.startswith("[["):
            issues.append("overview 中文全文 property must be an Obsidian wikilink to the 中译 note")
        if zh_fulltext and ("/" in zh_fulltext or "\\" in zh_fulltext):
            issues.append("overview 中文全文 must use a short note wikilink without folder path")
        expected_alias = "|中文正文]]" if source_language == "zh" else "|中译笔记]]"
        if zh_fulltext and expected_alias not in zh_fulltext:
            alias = "中文正文" if source_language == "zh" else "中译笔记"
            issues.append(f"overview 中文全文 wikilink alias must be {alias}")
        if '原文PDF: "[[' not in frontmatter:
            issues.append("overview 原文PDF property must be an Obsidian wikilink")
        title_short = _property_value(frontmatter, "中文短标题") or title_zh
        expected_pdf = workspace.source_pdf_path(title_short)
        if not expected_pdf.is_file():
            issues.append(f"source PDF must use confirmed short-title filename: {expected_pdf}")
        if source_language == "en":
            expected_mineru = workspace.mineru_source_path(title_short)
            if 'MinerU原文: "[[' not in frontmatter:
                issues.append("overview MinerU原文 property must be an Obsidian wikilink")
            if not expected_mineru.is_file():
                issues.append(f"English MinerU source must use confirmed short-title filename: {expected_mineru}")
        elif _has_property(frontmatter, "MinerU原文"):
            issues.append("Chinese source must merge MinerU into 【中译】 and must not expose a separate MinerU原文 property")
        for forbidden in ["质量报告", "来源锚点"]:
            if _has_property(frontmatter, forbidden):
                issues.append(f"overview must not expose raw JSON property: {forbidden}")
        for role in ["中译"]:
            for note in workspace.reading_workspace_path.glob(f"【{role}】*.md"):
                note_frontmatter = _frontmatter(note.read_text(encoding="utf-8-sig", errors="replace"))
                if _has_property(note_frontmatter, "Zotero条目链接"):
                    issues.append(f"{note.name} must not contain Zotero条目链接; use Zotero PDF链接 only")
                note_pdf = _property_value(note_frontmatter, "Zotero PDF链接")
                if zotero_pdf and note_pdf != zotero_pdf:
                    issues.append(f"{note.name} Zotero PDF链接 must match overview")
    legacy_files = [
        workspace.source_path / "原文.pdf",
        workspace.source_path / "MinerU英文全文.md",
        workspace.source_path / "MinerU中文全文.md",
    ]
    for legacy in legacy_files:
        if legacy.exists():
            issues.append(f"legacy source filename retained: {legacy}")
    vault_root = _find_vault_root(workspace.root_path)
    checked_targets: set[str] = set()
    for note in sorted(workspace.root_path.rglob("*.md")):
        text = note.read_text(encoding="utf-8-sig", errors="replace")
        for target in path_qualified_wikilink_targets(text):
            relative = note.relative_to(workspace.root_path).as_posix()
            issues.append(
                f"{relative} contains path-qualified Wikilink target; "
                f"use a short filename without folders: {target}"
            )
        if vault_root:
            for target in wikilink_targets(text):
                if target in checked_targets or "/" in target or "\\" in target:
                    continue
                checked_targets.add(target)
                matches = _target_matches(vault_root, target)
                if len(matches) > 1:
                    issues.append(
                        f"ambiguous short Wikilink target appears {len(matches)} times in the Vault: {target}"
                    )
    return issues


def workspace_status(workspace_root: Path) -> str:
    return "pass" if not validate_workspace_contract(workspace_root) else "fail"
