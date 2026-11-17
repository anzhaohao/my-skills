#!/usr/bin/env python3
"""Validate a basic Pastlines project and print graph quality statistics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EDGE_KINDS = {"pending", "causal", "temporal", "comparison", "membership"}
ASCII_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
PROJECT_KEYS = {
    "format",
    "schemaVersion",
    "appVersion",
    "projectId",
    "title",
    "createdAt",
    "updatedAt",
    "revision",
    "graph",
    "assets",
    "viewport",
    "appearance",
}
NODE_KEYS = {"id", "name", "type", "time", "description", "source", "x", "y", "imageIds", "color"}
EDGE_KEYS = {"id", "from", "to", "kind", "label"}
STYLE_KEYS = {"format", "version", "id", "name", "colors", "metrics", "resources", "backgroundImage"}
COLOR_KEYS = {
    "canvas",
    "workspace",
    "card",
    "cardBorder",
    "text",
    "mutedText",
    "line",
    "arrow",
    "selected",
    "hover",
    "pending",
    "cutPoint",
    "removed",
    "error",
    "button",
    "buttonText",
    "input",
    "panel",
    "notice",
    "overlay",
}
METRIC_KEYS = {
    "fontSize",
    "nodeFontSize",
    "lineHeight",
    "fontWeight",
    "gap",
    "padding",
    "radius",
    "borderWidth",
    "shadow",
    "lineWidth",
    "removedOpacity",
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"找不到文件：{path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败：{path}：{exc}")


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value


def validate_style(style, errors: list[str]) -> None:
    if not isinstance(style, dict):
        errors.append("appearance.snapshot 必须是对象")
        return
    if set(style) != STYLE_KEYS:
        errors.append(f"样式字段不正确：{sorted(set(style) ^ STYLE_KEYS)}")
    if style.get("format") != "pastlines-style" or style.get("version") != 1:
        errors.append("样式 format/version 不正确")
    if not isinstance(style.get("colors"), dict) or set(style.get("colors", {})) != COLOR_KEYS:
        errors.append("样式 colors 字段不正确")
    else:
        for key, value in style["colors"].items():
            if key == "overlay":
                if not isinstance(value, str) or not re.fullmatch(
                    r"rgba\(\s*\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*(?:0?\.\d+|0|1)\s*\)", value
                ):
                    errors.append("overlay 必须是安全的 rgba 颜色")
            elif not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                errors.append(f"颜色 {key} 必须是 #RRGGBB")
    if not isinstance(style.get("metrics"), dict) or set(style.get("metrics", {})) != METRIC_KEYS:
        errors.append("样式 metrics 字段不正确")
    if style.get("resources") != {}:
        errors.append("基础图谱样式 resources 应为空对象")
    if style.get("backgroundImage") is not None:
        errors.append("基础图谱不支持背景图片")


def main() -> int:
    parser = argparse.ArgumentParser(description="校验基础 Pastlines 项目")
    parser.add_argument("project", type=Path)
    parser.add_argument("--require-sources", action="store_true", help="要求每个节点 source 非空")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        project = load_json(args.project)
    except ValueError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1

    if not isinstance(project, dict):
        errors.append("项目根节点必须是对象")
        project = {}
    if set(project) != PROJECT_KEYS:
        errors.append(f"项目字段不正确：{sorted(set(project) ^ PROJECT_KEYS)}")
    if project.get("format") != "pastlines-project":
        errors.append("format 必须是 pastlines-project")
    if project.get("schemaVersion") != "1.1":
        errors.append("schemaVersion 必须是 1.1")
    if not isinstance(project.get("appVersion"), str) or not project["appVersion"].strip():
        errors.append("appVersion 不能为空")
    if not isinstance(project.get("projectId"), str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", project.get("projectId", "")
    ):
        errors.append("projectId 不是标准 UUID")
    if not isinstance(project.get("title"), str) or not project["title"].strip():
        errors.append("title 不能为空")
    if isinstance(project.get("revision"), bool) or not isinstance(project.get("revision"), int) or project["revision"] < 0:
        errors.append("revision 必须是非负整数")
    for key in ("createdAt", "updatedAt"):
        if not isinstance(project.get(key), str):
            errors.append(f"{key} 必须是字符串")
    graph = project.get("graph")
    if not isinstance(graph, dict) or set(graph) != {"nodes", "edges"}:
        errors.append("graph 必须只含 nodes 和 edges")
        graph = {"nodes": [], "edges": []}
    if not isinstance(graph["nodes"], list) or not isinstance(graph["edges"], list):
        errors.append("graph.nodes 和 graph.edges 必须是数组")
        graph = {"nodes": [], "edges": []}
    if not isinstance(project.get("assets"), dict):
        errors.append("assets 必须是对象")
    if project.get("assets") != {}:
        errors.append("基础图谱 assets 应为空对象")
    viewport = project.get("viewport")
    if not isinstance(viewport, dict) or set(viewport) != {"x", "y", "zoom"}:
        errors.append("viewport 必须只含 x、y、zoom")
    else:
        for key in ("x", "y", "zoom"):
            if not is_number(viewport.get(key)):
                errors.append(f"viewport.{key} 必须是数字")
        if is_number(viewport.get("zoom")) and not (0.1 <= viewport["zoom"] <= 5):
            errors.append("viewport.zoom 必须在 0.1—5")
    appearance = project.get("appearance")
    if not isinstance(appearance, dict) or set(appearance) != {"styleId", "snapshot"}:
        errors.append("appearance 必须只含 styleId 和 snapshot")
    else:
        if not isinstance(appearance.get("styleId"), str) or not appearance["styleId"]:
            errors.append("appearance.styleId 不能为空")
        validate_style(appearance.get("snapshot"), errors)

    node_ids = set()
    for index, node in enumerate(graph["nodes"], start=1):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] 必须是对象")
            continue
        if set(node) != NODE_KEYS:
            errors.append(f"nodes[{index}] 字段不正确：{sorted(set(node) ^ NODE_KEYS)}")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not ASCII_ID.fullmatch(node_id):
            errors.append(f"nodes[{index}].id 无效")
        elif node_id in node_ids:
            errors.append(f"节点 ID 重复：{node_id}")
        else:
            node_ids.add(node_id)
        if not isinstance(node.get("name"), str) or not node["name"].strip():
            errors.append(f"nodes[{index}].name 不能为空")
        if not isinstance(node.get("source"), str):
            errors.append(f"nodes[{index}].source 必须是字符串")
        elif args.require_sources and not node["source"].strip():
            errors.append(f"nodes[{index}].source 不能为空")
        for key in ("x", "y"):
            if not is_number(node.get(key)):
                errors.append(f"nodes[{index}].{key} 必须是数字")
        if not isinstance(node.get("imageIds"), list):
            errors.append(f"nodes[{index}].imageIds 必须是数组")
        if node.get("color") not in ("", None) and not (
            isinstance(node.get("color"), str) and re.fullmatch(r"#[0-9a-fA-F]{6}", node["color"])
        ):
            errors.append(f"nodes[{index}].color 必须是空字符串或 #RRGGBB")

    edge_ids = set()
    degree = {node_id: 0 for node_id in node_ids}
    kinds = {kind: 0 for kind in EDGE_KINDS}
    for index, edge in enumerate(graph["edges"], start=1):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}] 必须是对象")
            continue
        if set(edge) != EDGE_KEYS:
            errors.append(f"edges[{index}] 字段不正确：{sorted(set(edge) ^ EDGE_KEYS)}")
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not ASCII_ID.fullmatch(edge_id):
            errors.append(f"edges[{index}].id 无效")
        elif edge_id in edge_ids:
            errors.append(f"关系 ID 重复：{edge_id}")
        else:
            edge_ids.add(edge_id)
        source = edge.get("from")
        target = edge.get("to")
        if source not in node_ids or target not in node_ids:
            errors.append(f"edges[{index}] 引用了不存在的节点")
        else:
            degree[source] += 1
            degree[target] += 1
        if edge.get("kind") not in EDGE_KINDS:
            errors.append(f"edges[{index}].kind 不支持：{edge.get('kind')}")
        else:
            kinds[edge["kind"]] += 1
        if not isinstance(edge.get("label"), str):
            errors.append(f"edges[{index}].label 必须是字符串")

    if errors:
        print(
            json.dumps(
                {"ok": False, "errors": errors, "warnings": warnings},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    isolated = sorted(node_id for node_id, count in degree.items() if count == 0)
    if isolated:
        warnings.append(f"孤立节点：{', '.join(isolated)}")
    if len(graph["nodes"]) > 40:
        warnings.append("节点超过 40 个，建议拆图")
    if len(graph["nodes"]) > 24:
        warnings.append("节点超过 24 个，基础图可能偏密")
    result = {
        "ok": True,
        "title": project.get("title"),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "isolated": isolated,
        "edge_kinds": {kind: count for kind, count in kinds.items() if count},
        "node_source_coverage": 1.0
        if not graph["nodes"]
        else sum(1 for node in graph["nodes"] if str(node.get("source", "")).strip()) / len(graph["nodes"]),
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
