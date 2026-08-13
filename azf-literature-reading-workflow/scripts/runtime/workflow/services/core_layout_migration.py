from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from workflow.models.paper import PaperWorkspace, mineru_source_filename, source_pdf_filename
from workflow.services.artifact_runs import (
    ensure_artifact_run,
    finalize_artifact_run,
    latest_successful_state_dir,
)
from workflow.services.zh_fulltext import build_chinese_source_fulltext
from workflow.services.wikilinks import shorten_wikilink_targets
from workflow.services.zotero_links import read_workspace_zotero_pdf_link


AUXILIARY_RE = re.compile(r"^【(问答|图表|精读)】.*\.md$")
LEGACY_OVERVIEW_KEYS = {"质量报告", "来源锚点", "MinerU英文全文", "MinerU中文全文"}
OPTIONAL_NOTE_LINK_RE = re.compile(r"^\s*[-*]\s+.*\[\[【(?:问答|图表|精读)】")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _backup_file(path: Path, *, base: Path, backup_root: Path) -> Path:
    relative = path.resolve().relative_to(base.resolve())
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and file_sha256(target) != file_sha256(path):
        raise RuntimeError(f"backup target conflict: {target}")
    if not target.exists():
        shutil.copy2(path, target)
    if file_sha256(path) != file_sha256(target):
        raise RuntimeError(f"backup hash mismatch: {path}")
    return target


def _restore_exact_rename(target: Path, backup: Path) -> None:
    expected = file_sha256(backup)
    if not target.is_file():
        raise RuntimeError(f"renamed target missing: {target}")
    if file_sha256(target) != expected:
        shutil.copy2(backup, target)
    if file_sha256(target) != expected:
        raise RuntimeError(f"renamed target hash mismatch after restore: {target}")


def _set_frontmatter(lines: list[str], key: str, value: str | None) -> list[str]:
    rendered = f"{key}: {value}" if value is not None else None
    found = False
    output: list[str] = []
    for line in lines:
        if line.startswith(f"{key}:"):
            found = True
            if rendered is not None:
                output.append(rendered)
        else:
            output.append(line)
    if not found and rendered is not None:
        insert_at = next(
            (i for i, line in enumerate(output) if line.startswith(("aliases:", "tags:"))),
            len(output),
        )
        output.insert(insert_at, rendered)
    return output


def update_overview_text(
    text: str,
    *,
    title_zh: str,
    source_language: str,
    artifact_id: str,
) -> str:
    normalized = text.lstrip("\ufeff")
    if not normalized.startswith("---") or normalized.count("---") < 2:
        raise ValueError("overview must have one frontmatter block")
    _before, frontmatter, body = normalized.split("---", 2)
    lines = frontmatter.strip("\n").splitlines()
    for key in LEGACY_OVERVIEW_KEYS | {"已裁剪图表", "已精读"}:
        lines = _set_frontmatter(lines, key, None)
    pdf_name = source_pdf_filename(title_zh)
    mineru_name = mineru_source_filename(title_zh)
    lines = _set_frontmatter(lines, "中文短标题", f'"{title_zh}"')
    lines = _set_frontmatter(lines, "原文语言", source_language)
    lines = _set_frontmatter(lines, "原文PDF", f'"[[{pdf_name}|原文PDF]]"')
    lines = _set_frontmatter(lines, "外部产物ID", f'"{artifact_id}"')
    lines = _set_frontmatter(lines, "质量状态", "待验收")
    lines = _set_frontmatter(lines, "来源核对状态", "待核对")
    lines = _set_frontmatter(lines, "最近验收时间", '""')
    lines = _set_frontmatter(lines, "中译适用", str(source_language == "en").lower())
    lines = _set_frontmatter(lines, "MinerU合并到中文正文", str(source_language == "zh").lower())
    if source_language == "en":
        lines = _set_frontmatter(lines, "MinerU原文", f'"[[{mineru_name}|MinerU原文]]"')
        zh_alias = "中译笔记"
    else:
        lines = _set_frontmatter(lines, "MinerU原文", None)
        zh_alias = "中文正文"
    lines = _set_frontmatter(lines, "中文全文", f'"[[【中译】{title_zh}.md|{zh_alias}]]"')

    replacements = {
        "附件/原文/原文.pdf": f"附件/原文/{pdf_name}",
        "附件/原文/MinerU英文全文.md": f"附件/原文/{mineru_name}",
        "附件/原文/MinerU中文全文.md": f"阅读工作台/【中译】{title_zh}.md",
        f"【原文】{title_zh}.md": f"【中译】{title_zh}.md",
        "|中文原文]]": "|中文正文]]",
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    kept: list[str] = []
    for line in body.splitlines():
        if OPTIONAL_NOTE_LINK_RE.match(line):
            continue
        if "quality-report.json" in line or "source-anchors.json" in line:
            continue
        if line.strip().startswith(("- 质量报告:", "- 来源锚点:")):
            continue
        kept.append(line)
    updated = "---\n" + "\n".join(lines).rstrip() + "\n---\n" + "\n".join(kept).rstrip() + "\n"
    return shorten_wikilink_targets(updated)


def _replace_json_strings(value, replacements: dict[str, str]):
    if isinstance(value, dict):
        return {key: _replace_json_strings(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_json_strings(item, replacements) for item in value]
    if isinstance(value, str):
        output = value
        for old, new in replacements.items():
            output = output.replace(old, new)
        return output
    return value


def _find_vault_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def _scan_auxiliary_inbound_links(notes: list[Path], vault_root: Path | None) -> dict[Path, dict[str, list[str]]]:
    results = {note: {"short": [], "path_qualified": []} for note in notes}
    if not notes or vault_root is None:
        return results
    targets: dict[Path, tuple[str, tuple[str, ...]]] = {}
    for note in notes:
        relative = note.resolve().relative_to(vault_root.resolve()).as_posix()
        path_tokens = (
            f"[[{relative}",
            f"[[{relative.removesuffix('.md')}",
        )
        targets[note] = (f"[[{note.stem}", path_tokens)
    for candidate in vault_root.rglob("*.md"):
        try:
            text = candidate.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for note, (short_token, path_tokens) in targets.items():
            if candidate.resolve() == note.resolve():
                continue
            label = candidate.resolve().relative_to(vault_root.resolve()).as_posix()
            if any(token in text for token in path_tokens):
                results[note]["path_qualified"].append(label)
            elif short_token in text:
                results[note]["short"].append(label)
    return results


def _operation(kind: str, source: Path, *, paper_root: Path, target: Path | None = None) -> dict:
    item = {
        "kind": kind,
        "source": str(source),
        "relative_source": source.resolve().relative_to(paper_root.resolve()).as_posix(),
        "size": source.stat().st_size,
        "sha256": file_sha256(source),
    }
    if target is not None:
        item["target"] = str(target)
    return item


def _chinese_merge_content(source: Path, *, title_zh: str, zotero_pdf: str) -> str:
    raw = source.read_text(encoding="utf-8-sig", errors="replace")
    if raw.startswith("---") and raw.count("---") >= 2:
        raw = raw.split("---", 2)[2].lstrip()
    return build_chinese_source_fulltext(raw, title_zh=title_zh, zotero_pdf=zotero_pdf)


def _is_chinese_placeholder(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return "等待 MinerU 合并" in text or "尚未生成中文正文" in text


def _is_previous_mineru_embed_stub(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if "MinerU合并到中文正文: true" not in text or text.count("---") < 2:
        return False
    body = text.split("---", 2)[2].strip()
    return body.startswith("![[") and "MinerU中文全文.md" in body and len(body.splitlines()) <= 3


@dataclass(slots=True)
class WorkspaceMigrationResult:
    workspace: str
    title_zh: str
    source_language: str
    dry_run: bool
    operations: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    artifact_id: str | None = None


def migrate_workspace_core_layout(
    workspace_root: Path,
    *,
    paper_root: Path,
    artifact_root: Path,
    archive_root: Path,
    backup_root: Path,
    apply: bool = False,
) -> WorkspaceMigrationResult:
    workspace_root = workspace_root.resolve()
    paper_root = paper_root.resolve()
    workspace_root.relative_to(paper_root)
    paper = PaperWorkspace.from_root(workspace_root)
    title_zh = paper.title_zh
    language = paper.source_language if paper.source_language in {"en", "zh"} else "en"
    result = WorkspaceMigrationResult(str(workspace_root), title_zh, language, not apply)
    if not title_zh:
        result.issues.append("missing confirmed Chinese short title")
        return result
    if not paper.overview_note.is_file():
        result.issues.append(f"overview note missing: {paper.overview_note}")
        return result

    legacy_pdf = paper.source_path / "原文.pdf"
    target_pdf = paper.source_path / source_pdf_filename(title_zh)
    legacy_mineru = paper.source_path / ("MinerU中文全文.md" if language == "zh" else "MinerU英文全文.md")
    target_mineru = paper.source_path / mineru_source_filename(title_zh)
    old_chinese_note = paper.reading_workspace_path / f"【原文】{title_zh}.md"
    target_chinese_note = paper.chinese_fulltext_path(title_zh)
    auxiliary = sorted(path for path in paper.reading_workspace_path.glob("*.md") if AUXILIARY_RE.match(path.name))
    archive_workspace = archive_root.resolve() / workspace_root.name
    legacy_state = workspace_root / "附件" / "状态"

    if legacy_pdf.is_file() and legacy_pdf != target_pdf:
        if target_pdf.exists() and file_sha256(target_pdf) != file_sha256(legacy_pdf):
            result.issues.append(f"PDF target conflict: {target_pdf}")
        else:
            result.operations.append(_operation("rename_pdf", legacy_pdf, paper_root=paper_root, target=target_pdf))
    elif not legacy_pdf.is_file() and not target_pdf.is_file():
        result.issues.append(f"source PDF missing: {legacy_pdf}")

    if language == "en":
        if legacy_mineru.is_file() and legacy_mineru != target_mineru:
            if target_mineru.exists() and file_sha256(target_mineru) != file_sha256(legacy_mineru):
                result.issues.append(f"MinerU target conflict: {target_mineru}")
            else:
                result.operations.append(
                    _operation("rename_mineru", legacy_mineru, paper_root=paper_root, target=target_mineru)
                )
        elif not legacy_mineru.is_file() and not target_mineru.is_file():
            result.issues.append(f"MinerU source missing: {legacy_mineru}")
    else:
        merge_source = legacy_mineru if legacy_mineru.is_file() else old_chinese_note
        if merge_source.is_file():
            merged = _chinese_merge_content(
                merge_source,
                title_zh=title_zh,
                zotero_pdf=read_workspace_zotero_pdf_link(paper.overview_note),
            )
            if (
                target_chinese_note.is_file()
                and target_chinese_note.resolve() != merge_source.resolve()
                and not _is_chinese_placeholder(target_chinese_note)
                and not _is_previous_mineru_embed_stub(target_chinese_note)
                and target_chinese_note.read_text(encoding="utf-8-sig", errors="replace") != merged
            ):
                result.issues.append(f"Chinese fulltext target is user-owned and differs: {target_chinese_note}")
            else:
                result.operations.append(
                    _operation("merge_chinese", merge_source, paper_root=paper_root, target=target_chinese_note)
                )
        elif not target_chinese_note.is_file():
            result.issues.append("Chinese MinerU/source note missing")
        for obsolete, kind in [
            (legacy_mineru, "remove_merged_mineru"),
            (old_chinese_note, "remove_old_chinese_note"),
        ]:
            if obsolete.is_file() and obsolete.resolve() != target_chinese_note.resolve():
                result.operations.append(_operation(kind, obsolete, paper_root=paper_root))

    inbound = _scan_auxiliary_inbound_links(auxiliary, _find_vault_root(paper_root))
    for note in auxiliary:
        target = archive_workspace / note.name
        if target.exists() and file_sha256(target) != file_sha256(note):
            result.issues.append(f"archive target conflict: {target}")
            continue
        operation = _operation("archive_auxiliary", note, paper_root=paper_root, target=target)
        operation["incoming_short_links"] = inbound[note]["short"]
        operation["incoming_path_links"] = inbound[note]["path_qualified"]
        result.operations.append(operation)
        if inbound[note]["path_qualified"]:
            result.issues.append(
                f"path-qualified inbound links require review before archiving {note.name}: "
                + ", ".join(inbound[note]["path_qualified"])
            )

    if legacy_state.is_dir():
        for source in sorted(path for path in legacy_state.rglob("*") if path.is_file()):
            operation = _operation("migrate_state", source, paper_root=paper_root)
            operation["state_relative"] = source.relative_to(legacy_state).as_posix()
            result.operations.append(operation)

    if result.issues or not apply:
        return result

    touched = [
        path
        for path in [legacy_pdf, legacy_mineru, old_chinese_note, target_chinese_note, paper.overview_note]
        if path.is_file()
    ]
    touched.extend(auxiliary)
    if legacy_state.is_dir():
        touched.extend(path for path in legacy_state.rglob("*") if path.is_file())
    backup_paths: dict[Path, Path] = {}
    for path in dict.fromkeys(touched):
        backup_paths[path] = _backup_file(path, base=paper_root, backup_root=backup_root)

    artifact_id, state_dir = ensure_artifact_run(artifact_root, workspace_root, new_run=True)
    result.artifact_id = artifact_id
    try:
        previous_state = latest_successful_state_dir(artifact_root, workspace_root)
        if previous_state and previous_state.resolve() != state_dir.resolve():
            shutil.copytree(previous_state, state_dir, dirs_exist_ok=True)

        if legacy_pdf.is_file() and legacy_pdf != target_pdf:
            target_pdf.parent.mkdir(parents=True, exist_ok=True)
            if not target_pdf.exists():
                shutil.move(str(legacy_pdf), str(target_pdf))
            else:
                legacy_pdf.unlink()
            _restore_exact_rename(target_pdf, backup_paths[legacy_pdf])
        if language == "en" and legacy_mineru.is_file() and legacy_mineru != target_mineru:
            if not target_mineru.exists():
                shutil.move(str(legacy_mineru), str(target_mineru))
            else:
                legacy_mineru.unlink()
            _restore_exact_rename(target_mineru, backup_paths[legacy_mineru])
        if language == "zh":
            merge_source = legacy_mineru if legacy_mineru.is_file() else old_chinese_note
            if merge_source.is_file():
                merged = _chinese_merge_content(
                    merge_source,
                    title_zh=title_zh,
                    zotero_pdf=read_workspace_zotero_pdf_link(paper.overview_note),
                )
                target_chinese_note.parent.mkdir(parents=True, exist_ok=True)
                target_chinese_note.write_text(merged, encoding="utf-8")
            for obsolete in [legacy_mineru, old_chinese_note]:
                if obsolete.is_file() and obsolete.resolve() != target_chinese_note.resolve():
                    obsolete.unlink()

        for note in auxiliary:
            target = archive_workspace / note.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.move(str(note), str(target))
            else:
                note.unlink()
            _restore_exact_rename(target, backup_paths[note])

        if legacy_state.is_dir():
            copied: list[tuple[Path, Path]] = []
            for source in sorted(path for path in legacy_state.rglob("*") if path.is_file()):
                relative = source.relative_to(legacy_state)
                target = state_dir / relative
                if target.exists() and file_sha256(target) != file_sha256(source):
                    target = state_dir / "legacy-vault" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    shutil.copy2(source, target)
                if file_sha256(source) != file_sha256(target):
                    raise RuntimeError(f"external state hash mismatch: {source}")
                copied.append((source, target))
            if len(copied) != sum(1 for path in legacy_state.rglob("*") if path.is_file()):
                raise RuntimeError(f"external state file count mismatch: {legacy_state}")
            shutil.rmtree(legacy_state)

        replacements = {
            "附件/原文/原文.pdf": f"附件/原文/{target_pdf.name}",
            "附件/原文/MinerU英文全文.md": f"附件/原文/{target_mineru.name}",
            "附件/原文/MinerU中文全文.md": f"阅读工作台/{target_chinese_note.name}",
            f"阅读工作台/【原文】{title_zh}.md": f"阅读工作台/{target_chinese_note.name}",
        }
        for state_json in state_dir.rglob("*.json"):
            try:
                payload = json.loads(state_json.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                continue
            state_json.write_text(
                json.dumps(_replace_json_strings(payload, replacements), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        overview_text = paper.overview_note.read_text(encoding="utf-8-sig", errors="replace")
        paper.overview_note.write_text(
            update_overview_text(
                overview_text,
                title_zh=title_zh,
                source_language=language,
                artifact_id=artifact_id,
            ),
            encoding="utf-8",
        )
        report_path = state_dir / "core-layout-migration.json"
        report_path.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "migrated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    **asdict(result),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        finalize_artifact_run(
            artifact_root,
            workspace_root,
            artifact_id,
            status="migration_complete",
            promote=False,
        )
    except Exception:
        finalize_artifact_run(
            artifact_root,
            workspace_root,
            artifact_id,
            status="failed",
            promote=False,
        )
        raise
    return result
