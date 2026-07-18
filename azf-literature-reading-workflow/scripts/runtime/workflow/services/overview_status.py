from __future__ import annotations

from pathlib import Path


STATUS_KEYS = ("外部产物ID", "质量状态", "来源核对状态", "最近验收时间")
LEGACY_JSON_KEYS = ("质量报告", "来源锚点")
RAW_JSON_NAMES = ("quality-report.json", "source-anchors.json", "translation-audit.json")


def update_overview_artifact_status(
    path: Path,
    *,
    artifact_id: str,
    quality_status: str,
    source_status: str,
    accepted_at: str,
) -> bool:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---") or text.count("---") < 2:
        raise RuntimeError(f"overview has no YAML frontmatter: {path}")
    _prefix, frontmatter, body = text.split("---", 2)
    values = {
        "外部产物ID": artifact_id,
        "质量状态": quality_status,
        "来源核对状态": source_status,
        "最近验收时间": accepted_at,
    }
    lines = frontmatter.strip("\r\n").splitlines()
    output: list[str] = []
    seen: set[str] = set()
    insertion_index: int | None = None
    for line in lines:
        key = line.split(":", 1)[0] if ":" in line and not line[:1].isspace() else ""
        if key in LEGACY_JSON_KEYS:
            continue
        if key in STATUS_KEYS:
            output.append(f'{key}: "{values[key]}"')
            seen.add(key)
            continue
        output.append(line)
        if key in {"MinerU英文全文", "MinerU中文全文"}:
            insertion_index = len(output)
    missing = [key for key in STATUS_KEYS if key not in seen]
    if missing:
        index = insertion_index if insertion_index is not None else len(output)
        for offset, key in enumerate(missing):
            output.insert(index + offset, f'{key}: "{values[key]}"')

    body_lines = []
    for line in body.splitlines():
        if any(name in line for name in RAW_JSON_NAMES):
            continue
        body_lines.append(line)
    updated = "---\n" + "\n".join(output).rstrip() + "\n---\n" + "\n".join(body_lines).lstrip("\r\n").rstrip() + "\n"
    if updated == text.lstrip("\ufeff"):
        return False
    path.write_text(updated, encoding="utf-8")
    return True

