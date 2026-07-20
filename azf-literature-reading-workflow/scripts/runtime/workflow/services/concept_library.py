from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# 当前约定：concept_library_root 本身就是中央扫盲班概念卡目录。
# 不在其下自动创建“入口和索引/”“概念卡/”等子目录。
TEMPLATE_FILE = "概念卡模板.md"
CONCEPT_TYPES = {
    "基础概念", "物理量", "物理机制", "实验现象", "测量方法",
    "数值算法", "数据表示", "实验器件", "工程问题",
}
CONCEPT_STATUSES = {"待整理", "已整理", "待合并", "待核对"}

DEFINITION_HEADINGS = {"一句话解释", "它是什么意思", "基础解释", "概念解释"}
MECHANISM_HEADINGS = {"物理或工程机制", "核心机制", "严格定义", "物理机制", "工程机制"}
ANALOGY_HEADINGS = {"通俗比喻", "新手比喻", "类比"}
PAPER_USE_HEADINGS = {"为什么对本文重要", "为什么对这篇论文重要", "在论文中的用法", "为什么重要"}
MISUNDERSTANDING_HEADINGS = {"常见误解", "常见翻车点", "易错点", "常见问题"}

PAPER_TOPICS = {
    "FROG - 任意飞秒脉冲表征": ["FROG", "脉冲表征"],
    "SHG-FROG - 二次谐波频率分辨光学门控": ["FROG", "SHG-FROG"],
    "Fiber Instability - 深度学习预测噪声驱动非线性不稳定性": ["非线性光纤", "深度学习"],
    "Soliton Mode - 基于孤子模式的少周期飞秒脉冲": ["少周期脉冲", "孤子模式"],
    "WLC Control - 深度强化学习控制白光连续谱生成": ["白光连续谱", "强化学习"],
}

DOMAIN_RULES = [
    ("人工智能与计算", ["神经网络", "深度学习", "强化学习", "卷积", "CNN", "训练", "模型", "损失函数", "智能体", "agent"]),
    ("数学与信号处理", ["傅里叶", "FFT", "Gabor", "Wigner", "相位恢复", "迭代", "拟合", "优化", "采样", "矩阵", "变换", "反演算法"]),
    ("实验器件与工程", ["光谱仪", "探测器", "滤光片", "分束", "压缩器", "窗口片", "CCD", "相机", "狭缝", "光栅", "装置", "光路"]),
    ("测量与表征", ["FROG", "trace", "测量", "表征", "自相关", "门控", "单发", "反演强度", "时频谱"]),
    ("超快与非线性光学", ["自相位调制", "色散", "啁啾", "孤子", "超连续", "非线性", "相位匹配", "脉冲", "克尔", "光谱展宽"]),
    ("物理与光学基础", ["相位", "频率", "波长", "强度", "偏振", "群延迟", "谱宽", "分辨率", "光场"]),
]

TYPE_RULES = [
    ("实验器件", ["光谱仪", "探测器", "滤光片", "分束", "压缩器", "窗口片", "CCD", "相机", "狭缝", "光栅", "装置"]),
    ("数值算法", ["算法", "变换", "恢复", "迭代", "拟合", "优化", "采样", "矩阵", "重采样"]),
    ("测量方法", ["FROG", "测量", "表征", "自相关", "门控", "单发"]),
    ("数据表示", ["trace", "矩阵", "曲线", "二维图", "等高线", "谱时图", "时频谱"]),
    ("物理机制", ["调制", "色散", "啁啾", "匹配", "聚焦", "电离", "非线性", "孤子", "展宽"]),
    ("物理量", ["相位", "频率", "波长", "强度", "延迟", "谱宽", "分辨率", "效率", "误差"]),
]


@dataclass(slots=True)
class ConceptSource:
    path: Path
    source_dir: Path
    paper_root: Path
    paper_name: str
    paper_link_target: str
    name: str
    frontmatter: dict[str, Any]
    body: str
    created: str
    modified: str

    @property
    def paper_link(self) -> str:
        return f"[[{self.paper_link_target}|{self.paper_name}]]"


@dataclass(slots=True)
class PlannedCard:
    name: str
    target: Path
    sources: list[ConceptSource]
    frontmatter: dict[str, Any]
    body: str
    source_hashes: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return render_frontmatter(self.frontmatter) + "\n" + self.body.strip() + "\n"


@dataclass(slots=True)
class MigrationPlan:
    vault_root: Path
    paper_root: Path
    target_root: Path
    template_target: Path
    source_dirs: list[Path]
    cards: list[PlannedCard]
    duplicate_groups: dict[str, list[str]]
    link_rewrites: list[dict[str, Any]]
    source_count: int
    canonical_count: int
    non_markdown_files: list[str]
    link_prefix: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vault_root": str(self.vault_root),
            "paper_root": str(self.paper_root),
            "target_root": str(self.target_root),
            "template_target": str(self.template_target),
            "source_dirs": [str(item) for item in self.source_dirs],
            "source_count": self.source_count,
            "canonical_count": self.canonical_count,
            "duplicate_group_count": len(self.duplicate_groups),
            "duplicate_groups": self.duplicate_groups,
            "link_rewrite_file_count": len(self.link_rewrites),
            "link_rewrites": self.link_rewrites,
            "non_markdown_files": self.non_markdown_files,
            "link_prefix": self.link_prefix,
            "cards": [
                {
                    "name": card.name,
                    "target": str(card.target),
                    "status": card.frontmatter.get("状态"),
                    "domains": card.frontmatter.get("领域", []),
                    "topics": card.frontmatter.get("主题", []),
                    "concept_type": card.frontmatter.get("概念类型"),
                    "related_papers": card.frontmatter.get("相关论文", []),
                    "sources": [str(source.path) for source in card.sources],
                    "source_hashes": card.source_hashes,
                }
                for card in self.cards
            ],
        }


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip().casefold()


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    stripped = text.lstrip("\ufeff\r\n")
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", stripped, flags=re.DOTALL)
    if not match:
        return {}, stripped.strip()
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, stripped[match.end() :].strip()


def split_sections(body: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^#\s+(.+?)\s*$", body))
    if not matches:
        return [("补充内容", body.strip())] if body.strip() else []
    output: list[tuple[str, str]] = []
    prefix = body[: matches[0].start()].strip()
    if prefix:
        output.append(("补充内容", prefix))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        output.append((match.group(1).strip(), body[start:end].strip()))
    return output


def scalar_or_first(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value is not None else ""


def list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    value_text = str(value).strip()
    return [value_text] if value_text else []


def source_dates(frontmatter: dict[str, Any], path: Path) -> tuple[str, str]:
    created = scalar_or_first(frontmatter.get("创建时间") or frontmatter.get("created"))
    modified = scalar_or_first(frontmatter.get("修改时间") or frontmatter.get("modified"))
    if not created:
        created = datetime.fromtimestamp(path.stat().st_ctime).isoformat(timespec="minutes")
    if not modified:
        modified = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes")
    return created, modified


def discover_concept_sources(paper_root: Path, vault_root: Path) -> tuple[list[ConceptSource], list[Path], list[str]]:
    sources: list[ConceptSource] = []
    source_dirs: list[Path] = []
    non_markdown: list[str] = []
    for source_dir in sorted(path for path in paper_root.rglob("扫盲班") if path.is_dir()):
        markdown_files = sorted(source_dir.rglob("*.md"))
        if not markdown_files:
            continue
        source_dirs.append(source_dir)
        paper_root_path = source_dir.parent
        paper_name = paper_root_path.name
        paper_link_target = (paper_root_path / "阅读工作台" / "总览").resolve().relative_to(vault_root.resolve()).as_posix()
        for item in source_dir.rglob("*"):
            if item.is_file() and item.suffix.lower() != ".md":
                non_markdown.append(str(item))
        for path in markdown_files:
            frontmatter, body = read_markdown(path)
            created, modified = source_dates(frontmatter, path)
            sources.append(
                ConceptSource(
                    path=path,
                    source_dir=source_dir,
                    paper_root=paper_root_path,
                    paper_name=paper_name,
                    paper_link_target=paper_link_target,
                    name=path.stem.strip(),
                    frontmatter=frontmatter,
                    body=body,
                    created=created,
                    modified=modified,
                )
            )
    return sources, source_dirs, non_markdown


def unique_ordered(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        key = normalize_name(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def infer_domains(name: str, body: str) -> list[str]:
    haystack = f"{name}\n{body}".casefold()
    domains = [domain for domain, keywords in DOMAIN_RULES if any(keyword.casefold() in haystack for keyword in keywords)]
    return domains[:3] or ["待分类"]


def infer_concept_type(name: str, body: str) -> str:
    haystack = f"{name}\n{body}".casefold()
    for concept_type, keywords in TYPE_RULES:
        if any(keyword.casefold() in haystack for keyword in keywords):
            return concept_type
    return "基础概念"


def infer_topics(sources: list[ConceptSource], name: str, body: str) -> list[str]:
    topics: list[str] = []
    for source in sources:
        topics.extend(PAPER_TOPICS.get(source.paper_name, []))
    haystack = f"{name}\n{body}".casefold()
    for keyword, topic in [("FROG", "FROG"), ("孤子", "孤子"), ("超连续", "超连续谱"), ("强化学习", "强化学习"), ("深度学习", "深度学习")]:
        if keyword.casefold() in haystack:
            topics.append(topic)
    return unique_ordered(topics)


def existing_aliases(source: ConceptSource) -> list[str]:
    aliases: list[str] = []
    for key in ("aliases", "别名", "缩写"):
        aliases.extend(list_value(source.frontmatter.get(key)))
    for key in ("term", "term_zh", "中文名"):
        value = scalar_or_first(source.frontmatter.get(key))
        if value and normalize_name(value) != normalize_name(source.name):
            aliases.append(value)
    return aliases


def english_name(sources: list[ConceptSource], name: str) -> str:
    for source in sources:
        for key in ("英文名", "term_en"):
            value = scalar_or_first(source.frontmatter.get(key))
            if value:
                return value
    if re.fullmatch(r"[\x00-\x7F]+", name):
        return name
    return ""


def longest_section(candidates: list[str]) -> str:
    cleaned = unique_ordered([item for item in candidates if item.strip()])
    return max(cleaned, key=len) if cleaned else ""


def merge_bullets(candidates: list[str]) -> str:
    lines: list[str] = []
    for candidate in candidates:
        for line in candidate.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            stripped = re.sub(r"^[-*+]\s+", "", stripped)
            lines.append(stripped)
    return "\n".join(f"- {item}" for item in unique_ordered(lines))


def migrate_single_body(source: ConceptSource) -> str:
    sections = split_sections(source.body)
    output: list[str] = []
    paper_uses: list[str] = []
    for heading, content in sections:
        if heading in PAPER_USE_HEADINGS:
            if content:
                paper_uses.append(content)
            continue
        output.extend([f"# {heading}", "", content, ""])
    if paper_uses:
        output.extend(["# 在不同论文中的用法", "", f"## {source.paper_link}", "", "\n\n".join(paper_uses), ""])
    return "\n".join(output).strip()


def merge_duplicate_bodies(sources: list[ConceptSource]) -> str:
    definitions: list[str] = []
    mechanisms: list[str] = []
    analogies: list[str] = []
    misunderstandings: list[str] = []
    paper_uses: list[tuple[ConceptSource, str]] = []
    extras: list[tuple[ConceptSource, str, str]] = []
    for source in sources:
        for heading, content in split_sections(source.body):
            if heading in DEFINITION_HEADINGS:
                definitions.append(content)
            elif heading in MECHANISM_HEADINGS:
                mechanisms.append(content)
            elif heading in ANALOGY_HEADINGS:
                analogies.append(content)
            elif heading in PAPER_USE_HEADINGS:
                paper_uses.append((source, content))
            elif heading in MISUNDERSTANDING_HEADINGS:
                misunderstandings.append(content)
            elif content:
                extras.append((source, heading, content))

    output: list[str] = []
    definition = longest_section(definitions)
    mechanism = longest_section(mechanisms)
    analogy = longest_section(analogies)
    misunderstanding = merge_bullets(misunderstandings)
    if definition:
        output.extend(["# 一句话解释", "", definition, ""])
    if mechanism:
        output.extend(["# 物理或工程机制", "", mechanism, ""])
    if analogy:
        output.extend(["# 通俗比喻", "", analogy, ""])
    if paper_uses:
        output.extend(["# 在不同论文中的用法", ""])
        for source, content in paper_uses:
            output.extend([f"## {source.paper_link}", "", content or "待补充。", ""])
    if misunderstanding:
        output.extend(["# 常见误解", "", misunderstanding, ""])
    if extras:
        output.extend(["# 补充内容", ""])
        for source, heading, content in extras:
            output.extend([f"## {source.paper_link} · {heading}", "", content, ""])
    return "\n".join(output).strip()


def render_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    ordered_keys = ["类型", "英文名", "aliases", "领域", "主题", "概念类型", "状态", "相关论文", "创建时间", "修改时间"]
    for key in ordered_keys:
        value = data.get(key)
        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in value)
            else:
                lines.append(f"{key}: []")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False) if value not in (None, '') else ''}")
    lines.append("---")
    return "\n".join(lines)


def build_planned_card(name: str, sources: list[ConceptSource], target_root: Path) -> PlannedCard:
    ordered_sources = sorted(sources, key=lambda item: (item.paper_name, str(item.path)))
    body = migrate_single_body(ordered_sources[0]) if len(ordered_sources) == 1 else merge_duplicate_bodies(ordered_sources)
    aliases = unique_ordered([alias for source in ordered_sources for alias in existing_aliases(source) if normalize_name(alias) != normalize_name(name)])
    related_papers = unique_ordered([source.paper_link for source in ordered_sources])
    created = min(source.created for source in ordered_sources)
    modified = max(source.modified for source in ordered_sources)
    status = "待核对" if len(ordered_sources) > 1 else ("已整理" if len(body) >= 120 else "待整理")
    frontmatter = {
        "类型": "概念卡",
        "英文名": english_name(ordered_sources, name),
        "aliases": aliases,
        "领域": infer_domains(name, body),
        "主题": infer_topics(ordered_sources, name, body),
        "概念类型": infer_concept_type(name, body),
        "状态": status,
        "相关论文": related_papers,
        "创建时间": created,
        "修改时间": modified,
    }
    source_hashes = {
        str(source.path): hashlib.sha256(source.path.read_bytes()).hexdigest() for source in ordered_sources
    }
    return PlannedCard(
        name=name,
        target=target_root / f"{name}.md",
        sources=ordered_sources,
        frontmatter=frontmatter,
        body=body,
        source_hashes=source_hashes,
    )


def target_link(name: str, link_prefix: str) -> str:
    return f"{link_prefix}/{name}"


def rewrite_wikilinks(text: str, canonical_names: dict[str, str], link_prefix: str) -> tuple[str, int]:
    count = 0
    pattern = re.compile(r"\[\[([^\]|]+?)(#[^\]|]+)?(?:\|([^\]]+))?\]\]")

    def replacement(match: re.Match[str]) -> str:
        nonlocal count
        raw_target = match.group(1)
        heading = match.group(2) or ""
        display = match.group(3)
        normalized_target = raw_target.replace("\\", "/")
        if "扫盲班/" not in normalized_target:
            return match.group(0)
        stem = Path(normalized_target).stem
        canonical = canonical_names.get(normalize_name(stem))
        if not canonical:
            return match.group(0)
        new_target = target_link(canonical, link_prefix) + heading
        if normalized_target + heading == new_target:
            return match.group(0)
        count += 1
        return f"[[{new_target}|{display or stem}]]"

    return pattern.sub(replacement, text), count


def scan_link_rewrites(vault_root: Path, canonical_names: dict[str, str], excluded_dirs: list[Path], link_prefix: str) -> list[dict[str, Any]]:
    excluded = [path.resolve() for path in excluded_dirs]
    changes: list[dict[str, Any]] = []
    for path in vault_root.rglob("*.md"):
        resolved = path.resolve()
        if any(resolved == root or root in resolved.parents for root in excluded):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        _, count = rewrite_wikilinks(text, canonical_names, link_prefix)
        if count:
            changes.append({"path": str(path), "rewrite_count": count})
    return changes


def build_migration_plan(vault_root: Path, paper_root: Path, target_root: Path, template_target: Path) -> MigrationPlan:
    link_prefix = target_root.resolve().relative_to(vault_root.resolve()).as_posix()
    sources, source_dirs, non_markdown = discover_concept_sources(paper_root, vault_root)
    grouped: dict[str, list[ConceptSource]] = {}
    canonical_names: dict[str, str] = {}
    for source in sources:
        key = normalize_name(source.name)
        grouped.setdefault(key, []).append(source)
        canonical_names.setdefault(key, source.name)
    cards = [build_planned_card(canonical_names[key], group, target_root) for key, group in sorted(grouped.items(), key=lambda item: canonical_names[item[0]].casefold())]
    duplicates = {
        canonical_names[key]: [str(source.path) for source in group]
        for key, group in grouped.items()
        if len(group) > 1
    }
    link_rewrites = scan_link_rewrites(paper_root, canonical_names, source_dirs, link_prefix)
    return MigrationPlan(
        vault_root=vault_root,
        paper_root=paper_root,
        target_root=target_root,
        template_target=template_target,
        source_dirs=source_dirs,
        cards=cards,
        duplicate_groups=duplicates,
        link_rewrites=link_rewrites,
        source_count=len(sources),
        canonical_count=len(cards),
        non_markdown_files=non_markdown,
        link_prefix=link_prefix,
    )


def render_templater_template() -> str:
    return """---
类型: 概念卡
英文名:
aliases: []
领域: []
主题: []
概念类型:
状态: 待整理
相关论文: []
创建时间: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
修改时间: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
---

# 一句话解释

# 核心直觉

# 严格定义

# 在不同论文中的用法

# 易混概念

# 相关概念

# 待核对
"""


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content.rstrip() + "\n", encoding="utf-8")
    temp.replace(path)


def stage_plan(plan: MigrationPlan, staging_root: Path) -> None:
    if staging_root.exists():
        shutil.rmtree(staging_root)
    for card in plan.cards:
        relative = card.target.relative_to(plan.target_root)
        write_text_atomic(staging_root / relative, card.render())
    write_text_atomic(staging_root / "templater" / TEMPLATE_FILE, render_templater_template())


def write_report(plan: MigrationPlan, json_path: Path, markdown_path: Path) -> None:
    write_text_atomic(json_path, json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    duplicate_rows = "\n".join(
        f"| {name} | {len(paths)} | `{'`<br>`'.join(paths)}` |" for name, paths in sorted(plan.duplicate_groups.items())
    ) or "| 无 | 0 | - |"
    markdown = f"""# 概念卡迁移 Dry Run

- 源概念卡：{plan.source_count}
- 规范概念卡：{plan.canonical_count}
- 同名重复组：{len(plan.duplicate_groups)}
- 需要改写链接的文件：{len(plan.link_rewrites)}
- 非 Markdown 文件：{len(plan.non_markdown_files)}
- 目标目录：`{plan.target_root}`
- Templater 模板：`{plan.template_target}`

# 目标结构

```text
<concept_library_root>/
├── 概念A.md
├── 概念B.md
└── ...
```

# 同名重复项

| 概念 | 数量 | 来源 |
| --- | ---: | --- |
{duplicate_rows}

# 安全门

- Dry-run 不修改 Obsidian vault。
- Apply 前要求源目录全部为 Markdown 文件。
- 先写入中央概念卡并更新显式路径链接，再验证，最后把论文内部 `扫盲班/` 移入 vault 外的回滚归档。
- 同名重复项机械合并后标记为 `待核对`，保留各论文中的用法。
- 中央扫盲班根目录只放概念卡，不自动生成入口笔记、Base 或子文件夹；规则保存在项目和 Skill 中。
"""
    write_text_atomic(markdown_path, markdown)


def validate_staging(plan: MigrationPlan, staging_root: Path) -> list[str]:
    issues: list[str] = []
    staged_cards = list(staging_root.glob("*.md"))
    if len(staged_cards) != plan.canonical_count:
        issues.append(f"staged card count mismatch: {len(staged_cards)} != {plan.canonical_count}")
    if not (staging_root / "templater" / TEMPLATE_FILE).is_file():
        issues.append("missing staged Templater template")
    for path in staged_cards:
        frontmatter, _ = read_markdown(path)
        if frontmatter.get("类型") != "概念卡":
            issues.append(f"invalid concept type: {path}")
        if not isinstance(frontmatter.get("相关论文"), list) or not frontmatter.get("相关论文"):
            issues.append(f"missing related papers: {path}")
        if frontmatter.get("概念类型") not in CONCEPT_TYPES:
            issues.append(f"invalid concept type value: {path}")
        if frontmatter.get("状态") not in CONCEPT_STATUSES:
            issues.append(f"invalid concept status value: {path}")
    return issues


def _require_under(path: Path, root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root.expanduser().resolve())
    except ValueError as exc:
        raise RuntimeError(f"{label} is outside allowed root: {resolved}") from exc
    return resolved


def unresolved_local_sweeper_links(vault_root: Path, excluded_dirs: list[Path] | None = None) -> list[str]:
    excluded = [path.resolve() for path in (excluded_dirs or [])]
    issues: list[str] = []
    pattern = re.compile(r"\[\[(?:\.\./)+扫盲班/[^\]]+\]\]")
    for path in vault_root.rglob("*.md"):
        resolved = path.resolve()
        if any(folder == resolved or folder in resolved.parents for folder in excluded):
            continue
        try:
            markdown = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for match in pattern.findall(markdown):
            issues.append(f"{path}: {match}")
    return issues


def apply_plan(
    plan: MigrationPlan,
    *,
    replace_existing: bool = False,
    archive_root: Path | None = None,
    archive_sources: bool = False,
    delete_sources: bool = False,
) -> dict[str, Any]:
    if plan.non_markdown_files:
        raise RuntimeError("source concept folders contain non-Markdown files; aborting apply")
    if archive_sources and delete_sources:
        raise RuntimeError("archive_sources and delete_sources are mutually exclusive")

    vault_root = plan.vault_root.resolve()
    paper_root = _require_under(plan.paper_root, vault_root, "paper root")
    target_root = _require_under(plan.target_root, vault_root, "target root")
    _require_under(plan.template_target, vault_root, "template target")

    archive = archive_root.expanduser().resolve() if archive_root else None
    if archive is not None:
        try:
            archive.relative_to(vault_root)
        except ValueError:
            pass
        else:
            raise RuntimeError("rollback archive must be outside the Obsidian vault")

    existing_backup: Path | None = None
    if target_root.exists() and any(target_root.iterdir()):
        if not replace_existing:
            raise RuntimeError(f"target concept library is not empty: {target_root}")
        if archive is None:
            raise RuntimeError("archive_root is required when replacing an existing target")
        existing_backup = archive / "central-library-before-reconcile"
        if existing_backup.exists():
            raise RuntimeError(f"central-library backup already exists: {existing_backup}")
        existing_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target_root), str(existing_backup))

    archived_moves: list[tuple[Path, Path]] = []
    try:
        for card in plan.cards:
            write_text_atomic(card.target, card.render())
        write_text_atomic(plan.template_target, render_templater_template())

        canonical_names = {normalize_name(card.name): card.name for card in plan.cards}
        rewritten_files = 0
        rewritten_links = 0
        for change in plan.link_rewrites:
            path = Path(change["path"])
            original = path.read_text(encoding="utf-8-sig", errors="replace")
            updated, count = rewrite_wikilinks(original, canonical_names, plan.link_prefix)
            if count:
                write_text_atomic(path, updated)
                rewritten_files += 1
                rewritten_links += count

        validation_issues: list[str] = []
        final_cards = list(plan.target_root.glob("*.md"))
        if len(final_cards) != plan.canonical_count:
            validation_issues.append(f"final card count mismatch: {len(final_cards)} != {plan.canonical_count}")
        for card in plan.cards:
            if not card.target.is_file():
                validation_issues.append(f"missing target card: {card.target}")
        validation_issues.extend(unresolved_local_sweeper_links(paper_root, plan.source_dirs))
        if validation_issues:
            raise RuntimeError("; ".join(validation_issues))

        archived_dirs: list[str] = []
        deleted_dirs: list[str] = []
        for source_dir in plan.source_dirs:
            resolved = _require_under(source_dir, paper_root, "source concept directory")
            if resolved.name != "扫盲班":
                raise RuntimeError(f"unsafe source directory name: {resolved}")
            if target_root == resolved or target_root in resolved.parents:
                raise RuntimeError(f"source overlaps target: {resolved}")
            if archive_sources:
                if archive is None:
                    raise RuntimeError("archive_root is required when archiving sources")
                destination = archive / "paper-local-sweepers" / resolved.parent.name / resolved.name
                if destination.exists():
                    raise RuntimeError(f"source archive already exists: {destination}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(resolved), str(destination))
                archived_moves.append((destination, resolved))
                archived_dirs.append(str(destination))
            elif delete_sources:
                shutil.rmtree(resolved)
                deleted_dirs.append(str(resolved))

        return {
            "status": "pass",
            "cards_written": len(plan.cards),
            "rewritten_files": rewritten_files,
            "rewritten_links": rewritten_links,
            "archived_source_dirs": archived_dirs,
            "deleted_source_dirs": deleted_dirs,
            "target_root": str(plan.target_root),
            "template_target": str(plan.template_target),
            "existing_target_backup": str(existing_backup) if existing_backup else None,
        }
    except Exception:
        for archived_path, original_path in reversed(archived_moves):
            if archived_path.exists() and not original_path.exists():
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(archived_path), str(original_path))
        if existing_backup is not None and existing_backup.exists():
            failed_target = archive / "failed-new-central-library"
            if target_root.exists():
                if failed_target.exists():
                    shutil.rmtree(failed_target)
                shutil.move(str(target_root), str(failed_target))
            shutil.move(str(existing_backup), str(target_root))
        raise
