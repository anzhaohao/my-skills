from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

ALLOWED_TYPES = {
    "基础概念",
    "物理量",
    "物理机制",
    "实验现象",
    "测量方法",
    "数值算法",
    "数据表示",
    "实验器件",
    "工程问题",
}
ALLOWED_STATUS = {"待整理", "已整理", "待合并", "待核对"}
GENERIC_TAGS = {"concept", "concept-note", "glossary", "扫盲班"}

@dataclass(slots=True)
class SourceCard:
    path: Path
    source_dir: Path
    paper_root: Path
    paper_name: str
    name: str
    metadata: dict[str, Any]
    body: str

    @property
    def overview_link(self) -> str:
        reading = self.paper_root / "阅读工作台"
        candidates = sorted(reading.glob("【总览】*.md"))
        overview_stem = candidates[0].stem if candidates else "总览"
        return f"[[02-Brain Cells/0_论文精读/1_单篇论文/{self.paper_name}/阅读工作台/{overview_stem}]]"


@dataclass(slots=True)
class CanonicalCard:
    name: str
    sources: list[SourceCard]
    metadata: dict[str, Any]
    body: str
    status: str
    target_path: Path


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        output = value
    else:
        output = [value]
    seen: set[str] = set()
    result: list[str] = []
    for item in output:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _time_text(value: Any, fallback: datetime) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    if value not in (None, ""):
        return str(value)
    return fallback.isoformat(timespec="minutes")


def parse_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            data = yaml.safe_load(parts[1]) or {}
            if not isinstance(data, dict):
                data = {}
            return data, parts[2].lstrip("\r\n")
    return {}, text


def discover_source_cards(paper_root: Path, source_folder_name: str = "扫盲班") -> list[SourceCard]:
    root = paper_root.expanduser().resolve()
    source_dirs = sorted(p for p in root.rglob("*") if p.is_dir() and p.name == source_folder_name)
    cards: list[SourceCard] = []
    for source_dir in source_dirs:
        paper = source_dir.parent
        for path in sorted(p for p in source_dir.rglob("*.md") if p.is_file()):
            metadata, body = parse_markdown(path)
            cards.append(
                SourceCard(
                    path=path,
                    source_dir=source_dir,
                    paper_root=paper,
                    paper_name=paper.name,
                    name=path.stem,
                    metadata=metadata,
                    body=body,
                )
            )
    return cards


def normalized_name(name: str) -> str:
    return re.sub(r"[\s_\-—–·•（）()\[\]【】]+", "", name).casefold()


def source_classification(paper_name: str) -> tuple[list[str], list[str]]:
    if paper_name.startswith("FROG -") or paper_name.startswith("DeLong"):
        return ["超快光学"], ["FROG", "脉冲表征"]
    if paper_name.startswith("Chen Junyan"):
        return ["超快光学", "非线性光学"], ["少周期脉冲", "孤子模式"]
    if paper_name.startswith("Boussafa"):
        return ["非线性光学", "AI与计算方法"], ["光纤非线性", "不稳定性预测"]
    if paper_name.startswith("Valensise"):
        return ["非线性光学", "AI与计算方法"], ["超连续谱", "强化学习控制"]
    return [], []


def infer_concept_type(name: str, body: str) -> str:
    text = f"{name} {body[:1000]}".casefold()
    rules = [
        ("实验器件", ["探测器", "光谱仪", "滤光片", "窗口片", "分束", "相机", "狭缝", "压缩器", "晶体", "透镜", "反射镜", "位移台", "edfa", "ccd"]),
        ("数值算法", ["算法", "迭代", "拟合", "优化", "相位恢复", "反演", "神经网络", "ann", "cnn", "td3", "actor-critic", "fft", "变换", "投影法", "损失函数"]),
        ("数据表示", ["trace", "矩阵", "曲线", "等高线", "分布图", "谱图", "数据集", "采样网格", "残差", "直方图"]),
        ("测量方法", ["frog", "自相关", "测量", "表征", "门控", "检索", "标定", "验证方法"]),
        ("物理机制", ["效应", "自相位调制", "色散", "相位匹配", "啁啾", "衍射", "散射", "孤子", "不稳定性", "展宽", "压缩", "非线性", "四波混频"]),
        ("物理量", ["频率", "波长", "相位", "强度", "群延迟", "分辨率", "谱宽", "带宽", "能量", "功率", "效率", "时间宽度"]),
        ("实验现象", ["破裂", "漂移", "噪声", "失稳", "畸变", "饱和", "干涉条纹"]),
        ("工程问题", ["翻车", "限制", "权衡", "安全", "误差来源", "校准问题", "外推失败"]),
    ]
    for concept_type, keywords in rules:
        if any(keyword.casefold() in text for keyword in keywords):
            return concept_type
    return "基础概念"


def _existing_english_name(card: SourceCard) -> str:
    direct = card.metadata.get("英文名")
    if direct:
        return str(direct).strip()
    for key in ("title", "term"):
        value = card.metadata.get(key)
        if value and str(value).strip() != card.name and re.search(r"[A-Za-z]", str(value)):
            return str(value).strip()
    if re.fullmatch(r"[\x00-\x7F]+", card.name) and re.search(r"[A-Za-z]", card.name):
        return card.name
    for alias in _as_list(card.metadata.get("aliases")):
        if re.search(r"[A-Za-z]", alias):
            return alias
    return ""


def _body_key(body: str) -> str:
    normalized = re.sub(r"\s+", "", body).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _demote_headings(body: str, levels: int = 2) -> str:
    output: list[str] = []
    for line in body.strip().splitlines():
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match:
            count = min(6, len(match.group(1)) + levels)
            output.append("#" * count + match.group(2))
        else:
            output.append(line)
    return "\n".join(output).strip()


def build_canonical_cards(cards: list[SourceCard], target_dir: Path) -> tuple[list[CanonicalCard], dict[str, str], list[list[str]]]:
    groups: dict[str, list[SourceCard]] = defaultdict(list)
    for card in cards:
        groups[card.name].append(card)
    canonical_names = {name: name for name in groups}
    normalized_groups: dict[str, list[str]] = defaultdict(list)
    for name in groups:
        normalized_groups[normalized_name(name)].append(name)
    near_duplicates = [sorted(names) for names in normalized_groups.values() if len(names) > 1]

    output: list[CanonicalCard] = []
    for name, sources in sorted(groups.items(), key=lambda item: item[0].casefold()):
        sources = sorted(sources, key=lambda card: len(card.body), reverse=True)
        primary = sources[0]
        aliases: list[str] = []
        domains: list[str] = []
        topics: list[str] = []
        related: list[str] = []
        english_names: list[str] = []
        creation_values: list[tuple[str, datetime]] = []
        modification_values: list[tuple[str, datetime]] = []
        for source in sources:
            aliases.extend(_as_list(source.metadata.get("aliases")))
            aliases.extend(_as_list(source.metadata.get("别名")))
            for key in ("title", "term"):
                legacy = source.metadata.get(key)
                if legacy and str(legacy).strip() != name:
                    aliases.append(str(legacy).strip())
            domain_values, topic_values = source_classification(source.paper_name)
            domains.extend(_as_list(source.metadata.get("领域")) + domain_values)
            topics.extend(_as_list(source.metadata.get("主题")) + topic_values)
            related.extend(_as_list(source.metadata.get("相关论文")) + [source.overview_link])
            english = _existing_english_name(source)
            if english:
                english_names.append(english)
            stat = source.path.stat()
            creation_values.append((_time_text(source.metadata.get("创建时间") or source.metadata.get("created"), datetime.fromtimestamp(stat.st_ctime)), datetime.fromtimestamp(stat.st_ctime)))
            modification_values.append((_time_text(source.metadata.get("修改时间"), datetime.fromtimestamp(stat.st_mtime)), datetime.fromtimestamp(stat.st_mtime)))

        def unique(values: list[str]) -> list[str]:
            seen: set[str] = set()
            result: list[str] = []
            for value in values:
                value = str(value).strip()
                if value and value != name and value not in seen:
                    seen.add(value)
                    result.append(value)
            return result

        primary_body = primary.body.strip()
        known_keys = {_body_key(primary_body)}
        supplements: list[str] = []
        for source in sources[1:]:
            key = _body_key(source.body)
            if key in known_keys:
                continue
            known_keys.add(key)
            supplements.append(f"## {source.overview_link}\n\n{_demote_headings(source.body)}")
        if supplements:
            primary_body = primary_body.rstrip() + "\n\n# 从其他论文合并的补充\n\n" + "\n\n".join(supplements) + "\n"

        status = "待合并" if len(sources) > 1 and supplements else "已整理"
        if len(primary_body.strip()) < 250 or "待补充" in primary_body:
            status = "待整理" if len(sources) == 1 else "待合并"
        existing_statuses = [str(source.metadata.get("状态", "")).strip() for source in sources]
        if len(sources) == 1 and existing_statuses[0] in ALLOWED_STATUS:
            status = existing_statuses[0]

        metadata = {
            "类型": "概念卡",
            "英文名": unique(english_names)[0] if unique(english_names) else "",
            "aliases": unique(aliases),
            "领域": unique(domains),
            "主题": unique(topics),
            "概念类型": infer_concept_type(name, primary_body),
            "状态": status,
            "相关论文": unique(related),
            "创建时间": min(creation_values, key=lambda item: item[1])[0],
            "修改时间": max(modification_values, key=lambda item: item[1])[0],
        }
        output.append(
            CanonicalCard(
                name=name,
                sources=sources,
                metadata=metadata,
                body=primary_body.rstrip() + "\n",
                status=status,
                target_path=target_dir / f"{name}.md",
            )
        )
    return output, canonical_names, near_duplicates


def rewrite_concept_links(text: str, canonical_names: dict[str, str], central_link_prefix: str, rewrite_bare: bool = True) -> tuple[str, int]:
    count = 0
    wiki_pattern = re.compile(r"(!?)\[\[([^\]|#]+)(#[^\]|]+)?(\|[^\]]+)?\]\]")

    def replace_wiki(match: re.Match[str]) -> str:
        nonlocal count
        embed, target, fragment, alias = match.groups()
        normalized_target = target.replace("\\", "/").strip()
        base = Path(normalized_target).stem
        explicit_old = "扫盲班/" in normalized_target or normalized_target.startswith("../扫盲班") or normalized_target.startswith("./扫盲班")
        if base not in canonical_names or (not explicit_old and not rewrite_bare):
            return match.group(0)
        canonical = canonical_names[base]
        new_target = f"{central_link_prefix}/{canonical}{fragment or ''}"
        count += 1
        return f"{embed}[[{new_target}{alias or ''}]]"

    rewritten = wiki_pattern.sub(replace_wiki, text)
    markdown_pattern = re.compile(r"(\[[^\]]+\]\()([^\)]+扫盲班[/\\]([^\)#]+?)(?:\.md)?)(#[^\)]*)?(\))")

    def replace_markdown(match: re.Match[str]) -> str:
        nonlocal count
        prefix, _path, base, fragment, suffix = match.groups()
        name = Path(base).stem
        if name not in canonical_names:
            return match.group(0)
        count += 1
        target = f"{central_link_prefix}/{canonical_names[name]}.md"
        return f"{prefix}{target}{fragment or ''}{suffix}"

    rewritten = markdown_pattern.sub(replace_markdown, rewritten)
    return rewritten, count


def render_card(card: CanonicalCard, canonical_names: dict[str, str], central_link_prefix: str) -> str:
    body, _ = rewrite_concept_links(card.body, canonical_names, central_link_prefix, rewrite_bare=True)
    frontmatter = yaml.safe_dump(card.metadata, allow_unicode=True, sort_keys=False, width=120).strip()
    return f"---\n{frontmatter}\n---\n\n{body.rstrip()}\n"


def migration_report(cards: list[SourceCard], canonical: list[CanonicalCard], near_duplicates: list[list[str]], source_dirs: list[Path]) -> dict[str, Any]:
    duplicate_groups = [card for card in canonical if len(card.sources) > 1]
    return {
        "source_card_count": len(cards),
        "canonical_card_count": len(canonical),
        "source_directory_count": len(source_dirs),
        "exact_duplicate_group_count": len(duplicate_groups),
        "exact_duplicate_extra_files": sum(len(card.sources) - 1 for card in duplicate_groups),
        "near_duplicate_groups": near_duplicates,
        "status_counts": {
            status: sum(1 for card in canonical if card.status == status)
            for status in sorted(ALLOWED_STATUS)
        },
        "source_directories": [str(path) for path in source_dirs],
        "duplicate_groups": [
            {
                "name": card.name,
                "sources": [str(source.path) for source in card.sources],
                "status": card.status,
            }
            for card in duplicate_groups
        ],
        "cards": [
            {
                "name": card.name,
                "target": str(card.target_path),
                "status": card.status,
                "领域": card.metadata["领域"],
                "主题": card.metadata["主题"],
                "概念类型": card.metadata["概念类型"],
                "相关论文": card.metadata["相关论文"],
                "source_count": len(card.sources),
            }
            for card in canonical
        ],
    }


def write_canonical_cards(cards: list[CanonicalCard], canonical_names: dict[str, str], central_link_prefix: str) -> list[Path]:
    written: list[Path] = []
    for card in cards:
        card.target_path.parent.mkdir(parents=True, exist_ok=True)
        card.target_path.write_text(render_card(card, canonical_names, central_link_prefix), encoding="utf-8")
        written.append(card.target_path)
    return written


def update_paper_links(paper_roots: list[Path], source_dirs: list[Path], canonical_names: dict[str, str], central_link_prefix: str) -> dict[str, int]:
    resolved_sources = [source.resolve() for source in source_dirs]
    files_changed = 0
    links_changed = 0
    for paper_root in paper_roots:
        for path in paper_root.rglob("*.md"):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if any(source == resolved or source in resolved.parents for source in resolved_sources):
                continue
            original = path.read_text(encoding="utf-8-sig", errors="replace")
            rewritten, count = rewrite_concept_links(original, canonical_names, central_link_prefix, rewrite_bare=True)
            if count and rewritten != original:
                path.write_text(rewritten, encoding="utf-8")
                files_changed += 1
                links_changed += count
    return {"files_changed": files_changed, "links_changed": links_changed}


def validate_central_cards(target_dir: Path, expected_count: int) -> list[str]:
    issues: list[str] = []
    files = sorted(path for path in target_dir.glob("*.md") if path.is_file())
    if len(files) != expected_count:
        issues.append(f"canonical count mismatch: expected {expected_count}, got {len(files)}")
    names = [path.stem for path in files]
    if len(names) != len(set(names)):
        issues.append("duplicate canonical filenames remain")
    required = ["类型", "英文名", "aliases", "领域", "主题", "概念类型", "状态", "相关论文", "创建时间", "修改时间"]
    for path in files:
        metadata, _body = parse_markdown(path)
        for key in required:
            if key not in metadata:
                issues.append(f"{path}: missing property {key}")
        if metadata.get("类型") != "概念卡":
            issues.append(f"{path}: invalid 类型")
        if metadata.get("概念类型") not in ALLOWED_TYPES:
            issues.append(f"{path}: invalid 概念类型 {metadata.get('概念类型')}")
        if metadata.get("状态") not in ALLOWED_STATUS:
            issues.append(f"{path}: invalid 状态 {metadata.get('状态')}")
    return issues


def old_sweeper_link_issues(paper_roots: list[Path], central_link_prefix: str, ignored_dirs: list[Path] | None = None) -> list[str]:
    issues: list[str] = []
    ignored = [path.resolve() for path in (ignored_dirs or [])]
    pattern = re.compile(r"\[\[[^\]]*扫盲班[/\\][^\]]+\]\]")
    for root in paper_roots:
        for path in root.rglob("*.md"):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if any(directory == resolved or directory in resolved.parents for directory in ignored):
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for match in pattern.findall(text):
                if central_link_prefix not in match.replace("\\", "/"):
                    issues.append(f"{path}: {match}")
    return issues


def finalize_source_directories(source_dirs: list[Path], allowed_paper_root: Path) -> list[str]:
    allowed = allowed_paper_root.expanduser().resolve()
    removed: list[str] = []
    for source in source_dirs:
        resolved = source.expanduser().resolve()
        resolved.relative_to(allowed)
        if resolved.name != "扫盲班" or resolved.parent == allowed:
            raise ValueError(f"unsafe source directory: {resolved}")
        if resolved.is_dir():
            shutil.rmtree(resolved)
            removed.append(str(resolved))
    return removed


def save_report(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path