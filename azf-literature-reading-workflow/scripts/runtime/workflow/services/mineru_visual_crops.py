from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz

from workflow.models.source_anchor import SourceAnchor
from workflow.services.source_anchor_registry import SourceAnchorRegistry


@dataclass(slots=True)
class VisualRegion:
    asset_id: str
    source_type: str
    label: str
    page_index: int
    bbox: list[float]


def _walk_regions(node, page_index: int, counters: dict[str, int]) -> list[VisualRegion]:
    regions: list[VisualRegion] = []
    if isinstance(node, dict):
        block_type = node.get("type") or node.get("block_type")
        if block_type in {"image_body", "table_body"} and isinstance(node.get("bbox"), list):
            source_type = "table" if block_type == "table_body" else "figure"
            counters[source_type] += 1
            prefix = "Table" if source_type == "table" else "Fig"
            label = f"{prefix} {counters[source_type]}"
            asset_id = f"{source_type}-{counters[source_type]:02d}-p{page_index + 1:03d}"
            regions.append(
                VisualRegion(
                    asset_id=asset_id,
                    source_type=source_type,
                    label=label,
                    page_index=page_index,
                    bbox=[float(value) for value in node["bbox"][:4]],
                )
            )
        for value in node.values():
            regions.extend(_walk_regions(value, page_index, counters))
    elif isinstance(node, list):
        for value in node:
            regions.extend(_walk_regions(value, page_index, counters))
    return regions


def extract_regions(raw_json_path: Path) -> list[VisualRegion]:
    data = json.loads(raw_json_path.read_text(encoding="utf-8"))
    pages = data.get("pdf_info", [])
    counters = {"figure": 0, "table": 0}
    regions: list[VisualRegion] = []
    for fallback_index, page in enumerate(pages):
        page_index = int(page.get("page_idx", fallback_index))
        regions.extend(_walk_regions(page, page_index, counters))
    return _dedupe_regions(regions)


def _dedupe_regions(regions: list[VisualRegion]) -> list[VisualRegion]:
    seen: set[tuple[int, str, tuple[int, int, int, int]]] = set()
    deduped: list[VisualRegion] = []
    for region in regions:
        key = (
            region.page_index,
            region.source_type,
            tuple(int(round(value)) for value in region.bbox),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(region)

    counters = {"figure": 0, "table": 0}
    output: list[VisualRegion] = []
    for region in deduped:
        counters[region.source_type] += 1
        prefix = "Table" if region.source_type == "table" else "Fig"
        label = f"{prefix} {counters[region.source_type]}"
        output.append(
            VisualRegion(
                asset_id=f"{region.source_type}-{counters[region.source_type]:02d}-p{region.page_index + 1:03d}",
                source_type=region.source_type,
                label=label,
                page_index=region.page_index,
                bbox=region.bbox,
            )
        )
    return output


def _safe_stem(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]+", "-", label).strip("-")


def render_visual_crops(
    pdf_path: Path,
    raw_json_path: Path,
    figure_dir: Path,
    manifest_path: Path,
    anchor_path: Path,
    workspace_root: Path,
    target_long_edge: int = 4096,
) -> list[dict]:
    regions = extract_regions(raw_json_path)
    if not regions:
        return []

    figure_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    manifest: list[dict] = []
    registry = SourceAnchorRegistry(anchor_path)

    for region in regions:
        if region.page_index < 0 or region.page_index >= len(doc):
            continue
        page = doc[region.page_index]
        rect = fitz.Rect(region.bbox).intersect(page.rect)
        if rect.is_empty or rect.width <= 1 or rect.height <= 1:
            continue
        rect = (rect + (-4, -4, 4, 4)).intersect(page.rect)
        scale = max(2.0, min(8.0, target_long_edge / max(rect.width, rect.height)))
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
        prefix = "Table" if region.source_type == "table" else "Fig"
        sequence = region.label.split()[-1].zfill(2)
        file_name = f"{prefix}-{sequence}-p{region.page_index + 1:03d}-{_safe_stem(region.asset_id)}.png"
        output_path = figure_dir / file_name
        pix.save(output_path)

        item = {
            "asset_id": region.asset_id,
            "file_path": str(output_path),
            "source_pdf": str(pdf_path),
            "page": region.page_index + 1,
            "figure_label": region.label,
            "crop_method": "mineru_bbox_pdf_render",
            "clarity": "4k",
            "target_long_edge": target_long_edge,
            "crop_status": "success",
            "bbox": region.bbox,
        }
        manifest.append(item)
        registry.add(
            SourceAnchor(
                anchor_id=region.asset_id,
                paper_workspace=str(workspace_root),
                source_type=region.source_type,
                page=region.page_index + 1,
                section=region.label,
                figure_label=region.label,
                span_ref="MinerU raw output bbox",
                note_target=f"附件/图片/{file_name}",
                confidence="high",
                review_note="High-resolution crop generated from MinerU bbox and PDF render.",
            )
        )

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    registry.save()
    return manifest
