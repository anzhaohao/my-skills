#!/usr/bin/env python3
"""Convert a reviewable Pastlines graph plan into a schema-valid .pastlines file."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


EDGE_KINDS = {"pending", "causal", "temporal", "comparison", "membership"}
ASCII_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
CARD_WIDTH = 320
CARD_HEIGHT = 180
COLUMN_GAP = 40
ROW_GAP = 20


def fail(message: str) -> None:
    raise ValueError(message)


def require_text(value, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        fail(f"{field} 必须是字符串")
    value = value.strip()
    if not allow_empty and not value:
        fail(f"{field} 不能为空")
    return value


def finite_number(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"{field} 必须是数字")
    if value != value or value in (float("inf"), float("-inf")):
        fail(f"{field} 必须是有限数字")
    return float(value)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"找不到文件：{path}")
    except json.JSONDecodeError as exc:
        fail(f"JSON 解析失败：{path}：{exc}")


def load_style(style_path: Path | None) -> dict:
    path = style_path or Path(__file__).resolve().parent.parent / "assets" / "default-style.json"
    style = load_json(path)
    required = {"format", "version", "id", "name", "colors", "metrics", "resources", "backgroundImage"}
    if not isinstance(style, dict) or set(style) != required:
        fail(f"样式文件字段不正确：{path}")
    if style["format"] != "pastlines-style" or style["version"] != 1:
        fail(f"不支持的样式格式或版本：{path}")
    if not isinstance(style["colors"], dict) or not isinstance(style["metrics"], dict):
        fail(f"样式 colors/metrics 必须是对象：{path}")
    return style


def normalize_nodes(plan: dict) -> list[dict]:
    raw_nodes = plan.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        fail("plan.nodes 必须是非空数组")

    nodes = []
    seen = set()
    for index, item in enumerate(raw_nodes, start=1):
        if not isinstance(item, dict):
            fail(f"nodes[{index}] 必须是对象")
        node_id = require_text(item.get("id"), f"nodes[{index}].id")
        if not ASCII_ID.fullmatch(node_id):
            fail(f"nodes[{index}].id 只能用 ASCII 字母、数字、下划线、点和连字符")
        if node_id in seen:
            fail(f"节点 ID 重复：{node_id}")
        seen.add(node_id)
        if item.get("imageIds"):
            fail(f"基础图谱不嵌入图片；请把 nodes[{index}].imageIds 留空")
        node = {
            "id": node_id,
            "name": require_text(item.get("name"), f"nodes[{index}].name"),
            "type": require_text(item.get("type", ""), f"nodes[{index}].type", allow_empty=True),
            "time": require_text(item.get("time", ""), f"nodes[{index}].time", allow_empty=True),
            "description": require_text(
                item.get("description", ""), f"nodes[{index}].description", allow_empty=True
            ),
            "source": require_text(item.get("source"), f"nodes[{index}].source"),
            "imageIds": [],
            "color": "",
        }
        has_x = "x" in item
        has_y = "y" in item
        if has_x != has_y:
            fail(f"nodes[{index}] 的 x 和 y 必须同时提供")
        if has_x:
            node["x"] = finite_number(item["x"], f"nodes[{index}].x")
            node["y"] = finite_number(item["y"], f"nodes[{index}].y")
        nodes.append(node)
    return nodes


def normalize_edges(plan: dict, node_ids: set[str]) -> tuple[list[dict], list[str]]:
    raw_edges = plan.get("edges", [])
    if not isinstance(raw_edges, list):
        fail("plan.edges 必须是数组")

    edges = []
    evidence = []
    seen_ids = set()
    seen_pairs = set()
    for index, item in enumerate(raw_edges, start=1):
        if not isinstance(item, dict):
            fail(f"edges[{index}] 必须是对象")
        edge_id = item.get("id") or f"e{index:02d}"
        edge_id = require_text(edge_id, f"edges[{index}].id")
        if not ASCII_ID.fullmatch(edge_id):
            fail(f"edges[{index}].id 只能用 ASCII 字母、数字、下划线、点和连字符")
        if edge_id in seen_ids:
            fail(f"关系 ID 重复：{edge_id}")
        seen_ids.add(edge_id)
        source = require_text(item.get("from"), f"edges[{index}].from")
        target = require_text(item.get("to"), f"edges[{index}].to")
        if source not in node_ids or target not in node_ids:
            fail(f"edges[{index}] 引用了不存在的节点：{source} -> {target}")
        if source == target:
            fail(f"edges[{index}] 不能连接节点自身：{source}")
        kind = require_text(item.get("kind", "pending"), f"edges[{index}].kind")
        if kind not in EDGE_KINDS:
            fail(f"edges[{index}].kind 不支持：{kind}")
        pair = (source, target, kind)
        if pair in seen_pairs:
            fail(f"重复关系：{source} -> {target} ({kind})")
        seen_pairs.add(pair)
        evidence_text = require_text(item.get("evidence"), f"edges[{index}].evidence")
        edges.append(
            {
                "id": edge_id,
                "from": source,
                "to": target,
                "kind": kind,
                "label": require_text(item.get("label", ""), f"edges[{index}].label", allow_empty=True),
            }
        )
        evidence.append(evidence_text)
    return edges, evidence


def components(nodes: list[dict], edges: list[dict]) -> list[list[str]]:
    adjacency = {node["id"]: set() for node in nodes}
    for edge in edges:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    seen = set()
    result = []
    for node in nodes:
        start = node["id"]
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        members = []
        while stack:
            current = stack.pop()
            members.append(current)
            for other in sorted(adjacency[current]):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        result.append(members)
    return result


def compute_levels(node_ids: list[str], edges: list[dict]) -> dict[str, int]:
    incoming = {node_id: [] for node_id in node_ids}
    for edge in edges:
        incoming[edge["to"]].append(edge["from"])

    memo: dict[str, int] = {}

    def level(node_id: str, visiting: set[str]) -> int:
        if node_id in memo:
            return memo[node_id]
        if node_id in visiting:
            return 0
        visiting.add(node_id)
        parents = incoming[node_id]
        value = 0 if not parents else max(level(parent, visiting) + 1 for parent in parents)
        visiting.remove(node_id)
        memo[node_id] = min(value, len(node_ids) - 1)
        return memo[node_id]

    for node_id in node_ids:
        level(node_id, set())
    return memo


def layout_nodes(nodes: list[dict], edges: list[dict]) -> None:
    by_id = {node["id"]: node for node in nodes}
    groups = components(nodes, edges)
    offset_y = 60.0
    for group in groups:
        group_ids = set(group)
        group_edges = [
            edge
            for edge in edges
            if edge["from"] in group_ids and edge["to"] in group_ids
        ]
        levels = compute_levels(group, group_edges)
        grouped: dict[int, list[str]] = {}
        for node_id in group:
            grouped.setdefault(levels[node_id], []).append(node_id)
        max_rows = max((len(items) for items in grouped.values()), default=1)
        for level_index in sorted(grouped):
            for row, node_id in enumerate(grouped[level_index]):
                by_id[node_id]["x"] = 60.0 + level_index * (CARD_WIDTH + COLUMN_GAP)
                by_id[node_id]["y"] = offset_y + row * (CARD_HEIGHT + ROW_GAP)
        offset_y += max_rows * (CARD_HEIGHT + ROW_GAP) + 140


def fit_viewport(nodes: list[dict], width: int = 1440, height: int = 900) -> dict:
    if width <= 120 or height <= 120:
        fail("viewport 宽高必须大于 120")
    min_x = min(node["x"] for node in nodes)
    max_x = max(node["x"] + CARD_WIDTH for node in nodes)
    min_y = min(node["y"] for node in nodes)
    max_y = max(node["y"] + CARD_HEIGHT for node in nodes)
    graph_width = max(1.0, max_x - min_x)
    graph_height = max(1.0, max_y - min_y)
    available_width = width - 120
    available_height = height - 120
    zoom = min(1.0, available_width / graph_width, available_height / graph_height)
    zoom = max(0.1, min(5.0, round(zoom, 4)))
    return {
        "x": round(60 - min_x * zoom, 2),
        "y": round(60 - min_y * zoom, 2),
        "zoom": zoom,
    }


def build_project(
    plan: dict,
    style: dict,
    project_id: str | None = None,
    viewport_width: int = 1440,
    viewport_height: int = 900,
) -> tuple[dict, dict]:
    title = require_text(plan.get("title"), "plan.title")
    nodes = normalize_nodes(plan)
    edges, evidence = normalize_edges(plan, {node["id"] for node in nodes})
    if len(nodes) > 80:
        fail("节点超过 80 个；请拆成多个图谱")

    if any("x" not in node for node in nodes):
        layout_nodes(nodes, edges)

    viewport = fit_viewport(nodes, viewport_width, viewport_height)
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    project = {
        "format": "pastlines-project",
        "schemaVersion": "1.1",
        "appVersion": "1.42.0",
        "projectId": project_id or str(uuid.uuid4()),
        "title": title,
        "createdAt": now,
        "updatedAt": now,
        "revision": 0,
        "graph": {"nodes": nodes, "edges": edges},
        "assets": {},
        "viewport": viewport,
        "appearance": {"styleId": style["id"], "snapshot": style},
    }

    degree = {node["id"]: 0 for node in nodes}
    for edge in edges:
        degree[edge["from"]] += 1
        degree[edge["to"]] += 1
    isolated = [node["id"] for node in nodes if degree[node["id"]] == 0]
    kinds = {kind: sum(1 for edge in edges if edge["kind"] == kind) for kind in sorted(EDGE_KINDS)}
    summary = {
        "title": title,
        "nodes": len(nodes),
        "edges": len(edges),
        "isolated": isolated,
        "components": len(components(nodes, edges)),
        "edge_kinds": {kind: count for kind, count in kinds.items() if count},
        "viewport": viewport,
        "node_source_coverage": 1.0,
        "edge_evidence_coverage": 1.0 if len(evidence) == len(edges) else 0.0,
    }
    return project, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="把 Pastlines graph plan 转成 .pastlines 项目")
    parser.add_argument("plan", type=Path, help="输入 plan JSON")
    parser.add_argument("output", type=Path, help="输出 .pastlines 文件")
    parser.add_argument("--style", type=Path, help="可选样式 JSON；默认使用 assets/default-style.json")
    parser.add_argument("--project-id", help="可选固定 projectId，便于回归测试")
    parser.add_argument("--viewport-width", type=int, default=1440, help="目标内容区宽度，默认 1440")
    parser.add_argument("--viewport-height", type=int, default=900, help="目标内容区高度，默认 900")
    args = parser.parse_args()

    try:
        plan = load_json(args.plan)
        style = load_style(args.style)
        project, summary = build_project(
            plan,
            style,
            args.project_id,
            args.viewport_width,
            args.viewport_height,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(project, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary["output"] = str(args.output.resolve())
        print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
