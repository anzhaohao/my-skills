from __future__ import annotations

"""MinerU 4.x 解析产物归一化。

MinerU 4.0 起解析产物结构与 3.x 不同：

- ``mineru-kit parse <pdf> -o <dir> -f markdown`` 只产出扁平的 ``<stem>.md``；
- 图片以 ``![](data:image/...;base64,...)`` 内联进 Markdown，不再有 ``images/`` 目录；
- ``content_list.json`` 由 ``structured_content.json`` 取代，block 的 bbox 改成 0..1 归一化；
- middle JSON 顶层由 ``pdf_info`` 改为 ``pages``，block 结构也不同。

本模块把 4.x 产物还原成工作流既有的 3.x 目录契约，使下游
(``mineru_outputs`` / ``mineru_visual_crops`` / ``extract_highres_figures``) 无需改动：

    <out>/<stem>/auto/<stem>.md
    <out>/<stem>/auto/<stem>_middle.json          (pdf_info + para_blocks + 绝对点 bbox)
    <out>/<stem>/auto/<stem>_content_list.json
    <out>/<stem>/auto/<stem>_content_list_v2.json
    <out>/<stem>/auto/images/<sha256>.<ext>
"""

import base64
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

import fitz

_DATA_URI = re.compile(
    r"!\[([^\]]*)\]\(data:image/([A-Za-z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+)\)"
)
_SUBTYPE_EXT = {
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "webp": "webp",
    "gif": "gif",
    "bmp": "bmp",
    "tiff": "tiff",
}
_VISUAL_SOURCE_TYPES = {"image", "figure", "chart"}
_TABLE_SOURCE_TYPES = {"table"}


def page_sizes(pdf_path: Path) -> list[tuple[float, float]]:
    """Return each page's size in PDF points, in page order."""
    document = fitz.open(pdf_path)
    try:
        return [(float(page.rect.width), float(page.rect.height)) for page in document]
    finally:
        document.close()


def inline_images_to_files(markdown: str, images_dir: Path) -> str:
    """Write inline base64 images to ``images_dir`` and rewrite links to relative paths."""
    def replace(match: re.Match[str]) -> str:
        alt, subtype, payload = match.group(1), match.group(2).lower(), match.group(3)
        try:
            data = base64.b64decode(re.sub(r"\s+", "", payload), validate=False)
        except Exception:
            return match.group(0)
        if not data:
            return match.group(0)
        name = f"{hashlib.sha256(data).hexdigest()}.{_SUBTYPE_EXT.get(subtype, subtype)}"
        images_dir.mkdir(parents=True, exist_ok=True)
        target = images_dir / name
        if not target.exists():
            target.write_bytes(data)
        return f"![{alt}](images/{name})"

    return _DATA_URI.sub(replace, markdown)


def _size_for(sizes: list[tuple[float, float]], page_idx: int) -> tuple[float, float]:
    if 0 <= page_idx < len(sizes):
        return sizes[page_idx]
    return 0.0, 0.0


def _rescale_bboxes(node, width: float, height: float):
    """Recursively convert nested 0..1 bboxes to absolute PDF points.

    MinerU 4.x nests its original normalised blocks inside ``content``. Left as-is,
    ``extract_regions`` would report those nested blocks a second time with un-scaled
    coordinates.
    """
    if isinstance(node, dict):
        result = {}
        for key, value in node.items():
            if key == "bbox" and isinstance(value, list) and len(value) >= 4:
                values = [float(item) for item in value[:4]]
                if width > 0 and height > 0 and max(values) <= 1.5:
                    values = [values[0] * width, values[1] * height, values[2] * width, values[3] * height]
                result[key] = values
            else:
                result[key] = _rescale_bboxes(value, width, height)
        return result
    if isinstance(node, list):
        return [_rescale_bboxes(item, width, height) for item in node]
    return node


def _block_kind(block_type: str) -> str:
    if block_type in _VISUAL_SOURCE_TYPES:
        return "image_body"
    if block_type in _TABLE_SOURCE_TYPES:
        return "table_body"
    return block_type


def build_pdf_info(middle: dict, sizes: list[tuple[float, float]]) -> dict:
    """Convert 4.x ``pages``/``blocks`` into the 3.x ``pdf_info``/``para_blocks`` shape.

    ``mineru_visual_crops.extract_regions`` reads ``pdf_info[].para_blocks[]`` entries whose
    ``type`` is ``image_body``/``table_body`` and compares the bbox against ``page.rect``, so
    bboxes must be emitted in absolute PDF points.
    """
    pdf_info: list[dict] = []
    for index, page in enumerate(middle.get("pages") or []):
        if not isinstance(page, dict):
            continue
        page_idx = int(page.get("page_idx", index))
        width, height = _size_for(sizes, page_idx)
        para_blocks: list[dict] = []
        for block in page.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            bbox = block.get("bbox")
            if not (isinstance(bbox, list) and len(bbox) >= 4):
                continue
            values = [float(value) for value in bbox[:4]]
            if width > 0 and height > 0 and max(values) <= 1.5:
                values = [values[0] * width, values[1] * height, values[2] * width, values[3] * height]
            entry = {
                "type": _block_kind(str(block.get("type") or "").lower()),
                "bbox": values,
            }
            for key, value in block.items():
                if key not in {"type", "bbox"}:
                    entry[key] = _rescale_bboxes(value, width, height)
            para_blocks.append(entry)
        pdf_info.append({"page_idx": page_idx, "para_blocks": para_blocks})
    return {"pdf_info": pdf_info, "schema": "mineru4-normalized"}


def build_content_list(structured: dict, sizes: list[tuple[float, float]]) -> list[dict]:
    """Rebuild a 3.x-style content list (0..1000 bbox grid) from ``structured_content.json``."""
    rows: list[dict] = []
    for index, page in enumerate(structured.get("pages") or []):
        if not isinstance(page, dict):
            continue
        page_idx = int(page.get("page_idx", index))
        width, height = _size_for(sizes, page_idx)
        for block in page.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            bbox = block.get("bbox")
            if not (isinstance(bbox, list) and len(bbox) >= 4) or width <= 0 or height <= 0:
                continue
            values = [float(value) for value in bbox[:4]]
            if max(values) <= 1.5:
                values = [values[0] * 1000, values[1] * 1000, values[2] * 1000, values[3] * 1000]
            row: dict = {
                "type": block.get("type"),
                "page_idx": page_idx,
                "bbox": [round(value) for value in values],
            }
            content = block.get("content")
            if isinstance(content, str):
                row["text"] = content
            elif isinstance(content, list):
                parts = [str(item.get("content", "")) for item in content if isinstance(item, dict)]
                row["text"] = " ".join(part for part in parts if part)
            for key in ("img_path", "sub_type", "level", "captions", "footnotes", "continues_prev"):
                if key in block:
                    row[key] = block[key]
            rows.append(row)
    return rows


def _first(paths: list[Path]) -> Path | None:
    return paths[0] if paths else None


def publish_mineru4_bundle(
    staged_output: Path,
    output_dir: Path,
    pdf_path: Path,
    *,
    stem: str | None = None,
) -> Path | None:
    """Turn a 4.x run output into the legacy ``<stem>/auto/`` bundle. Returns the auto dir."""
    archives = sorted(path for path in staged_output.rglob("*.zip") if path.is_file())
    archive_path = _first(archives)
    if archive_path is None:
        return None
    resolved_stem = stem or pdf_path.stem
    auto_dir = output_dir / resolved_stem / "auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    unpacked = auto_dir / "_mineru4_raw"
    if unpacked.exists():
        shutil.rmtree(unpacked, ignore_errors=True)
    unpacked.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(unpacked)
        sizes = page_sizes(pdf_path)

        markdown_source = _first(sorted(unpacked.glob("*.md"))) or _first(sorted(unpacked.rglob("*.md")))
        if markdown_source is not None:
            markdown = markdown_source.read_text(encoding="utf-8", errors="replace")
            markdown = inline_images_to_files(markdown, auto_dir / "images")
            (auto_dir / f"{resolved_stem}.md").write_text(markdown, encoding="utf-8")

        unpacked_images = _first([path for path in sorted(unpacked.rglob("images")) if path.is_dir()])
        if unpacked_images is not None:
            shutil.copytree(unpacked_images, auto_dir / "images", dirs_exist_ok=True)

        middle_source = _first(sorted(unpacked.glob("middle_json.json"))) or _first(sorted(unpacked.rglob("middle_json.json")))
        if middle_source is not None:
            middle = json.loads(middle_source.read_text(encoding="utf-8", errors="replace"))
            normalized = build_pdf_info(middle, sizes)
            (auto_dir / f"{resolved_stem}_middle.json").write_text(
                json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        for name in ("structured_content.json", "model_output.json"):
            source = _first(sorted(unpacked.glob(name))) or _first(sorted(unpacked.rglob(name)))
            if source is not None:
                shutil.copy2(source, auto_dir / name)

        structured_path = auto_dir / "structured_content.json"
        if structured_path.is_file():
            structured = json.loads(structured_path.read_text(encoding="utf-8", errors="replace"))
            rows = build_content_list(structured, sizes)
            (auto_dir / f"{resolved_stem}_content_list.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (auto_dir / f"{resolved_stem}_content_list_v2.json").write_text(
                json.dumps({"version": 2, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    finally:
        shutil.rmtree(unpacked, ignore_errors=True)
    return auto_dir

