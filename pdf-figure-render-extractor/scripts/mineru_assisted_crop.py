#!/usr/bin/env python3
"""
Use MinerU extracted figures as visual anchors, then crop the same regions from
high-DPI PDF page renders.

Workflow:
  1. Render PDF pages at a moderate DPI for matching.
  2. Locate each MinerU image on the rendered pages with multi-scale template matching.
  3. Save normalized regions.json.
  4. Re-render and crop matched regions at high DPI.

Requires:
  pip install pymupdf pillow opencv-python numpy
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError as exc:
    print("Error: missing dependency:", exc)
    print("Install with: pip install pymupdf pillow opencv-python numpy")
    sys.exit(1)


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass
class Match:
    source: Path
    page: int
    score: float
    box: tuple[float, float, float, float]
    pixel_box: tuple[int, int, int, int]
    scaled_size: tuple[int, int]


def parse_pages(spec: str, total_pages: int) -> list[int]:
    """Return 1-based page numbers."""
    if spec.lower() == "all":
        return list(range(1, total_pages + 1))

    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))

    return sorted(p for p in pages if 1 <= p <= total_pages)


def find_images_dir(mineru_output: Path) -> Path:
    candidates = [
        mineru_output,
        mineru_output / "images",
        mineru_output / "auto" / "images",
    ]
    for candidate in candidates:
        if candidate.is_dir() and any(p.suffix.lower() in IMAGE_EXTS for p in candidate.iterdir()):
            return candidate
    raise FileNotFoundError(
        f"No MinerU image directory found under {mineru_output}. "
        "Expected an images directory or a directory containing image files."
    )


def list_images(images_dir: Path, min_size: int, min_dimension: int) -> list[Path]:
    images = []
    for path in sorted(images_dir.iterdir()):
        if path.suffix.lower() not in IMAGE_EXTS or not path.is_file():
            continue
        if min_size and path.stat().st_size < min_size:
            continue
        try:
            with Image.open(path) as img:
                width, height = img.size
        except Exception:
            continue
        if min_dimension and (width < min_dimension or height < min_dimension):
            continue
        images.append(path)
    return images


def render_page(doc: fitz.Document, page_num: int, dpi: int) -> Image.Image:
    page = doc[page_num - 1]
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def to_gray_array(image: Image.Image, max_width: int | None = None) -> np.ndarray:
    if max_width and image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, max(1, int(image.height * ratio))), Image.Resampling.LANCZOS)
    arr = np.array(image.convert("L"))
    return arr


def trim_white_margin(image: Image.Image, threshold: int = 250, padding: int = 2) -> Image.Image:
    gray = np.array(image.convert("L"))
    mask = gray < threshold
    if not mask.any():
        return image
    ys, xs = np.where(mask)
    x0 = max(int(xs.min()) - padding, 0)
    y0 = max(int(ys.min()) - padding, 0)
    x1 = min(int(xs.max()) + padding + 1, image.width)
    y1 = min(int(ys.max()) + padding + 1, image.height)
    return image.crop((x0, y0, x1, y1))


def build_scales(
    template_size: tuple[int, int],
    page_size: tuple[int, int],
    min_scale: float,
    max_scale: float,
    steps: int,
) -> list[float]:
    tw, th = template_size
    pw, ph = page_size
    upper = min(max_scale, pw / max(tw, 1), ph / max(th, 1))
    lower = max(min_scale, 0.05)
    if upper < lower:
        return []
    if steps <= 1:
        return [(lower + upper) / 2]
    return [float(x) for x in np.linspace(lower, upper, steps)]


def match_template_on_page(
    template_img: Image.Image,
    page_img: Image.Image,
    min_scale: float,
    max_scale: float,
    scale_steps: int,
    max_page_width: int,
) -> tuple[float, tuple[int, int, int, int], tuple[int, int]]:
    page_ratio = 1.0
    if page_img.width > max_page_width:
        page_ratio = max_page_width / page_img.width
        page_for_match = page_img.resize(
            (max_page_width, max(1, int(page_img.height * page_ratio))),
            Image.Resampling.LANCZOS,
        )
    else:
        page_for_match = page_img

    page_arr = to_gray_array(page_for_match)
    best_score = -1.0
    best_box = (0, 0, 0, 0)
    best_size = (0, 0)

    scales = build_scales(
        template_img.size,
        page_for_match.size,
        min_scale,
        max_scale,
        scale_steps,
    )

    for scale in scales:
        tw = max(8, int(template_img.width * scale))
        th = max(8, int(template_img.height * scale))
        if tw >= page_for_match.width or th >= page_for_match.height:
            continue

        templ = template_img.resize((tw, th), Image.Resampling.LANCZOS)
        templ_arr = to_gray_array(templ)
        result = cv2.matchTemplate(page_arr, templ_arr, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(result)

        if score > best_score:
            x0, y0 = loc
            x1, y1 = x0 + tw, y0 + th
            best_score = float(score)
            best_box = (
                int(round(x0 / page_ratio)),
                int(round(y0 / page_ratio)),
                int(round(x1 / page_ratio)),
                int(round(y1 / page_ratio)),
            )
            best_size = (
                int(round(tw / page_ratio)),
                int(round(th / page_ratio)),
            )

    return best_score, best_box, best_size


def normalized_box(pixel_box: tuple[int, int, int, int], page_size: tuple[int, int], padding: float) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = pixel_box
    width, height = page_size
    pad_x = padding * (x1 - x0)
    pad_y = padding * (y1 - y0)
    nx0 = max(0.0, (x0 - pad_x) / width)
    ny0 = max(0.0, (y0 - pad_y) / height)
    nx1 = min(1.0, (x1 + pad_x) / width)
    ny1 = min(1.0, (y1 + pad_y) / height)
    return (nx0, ny0, nx1, ny1)


def locate_mineru_images(
    pdf_path: Path,
    mineru_output: Path,
    pages: str,
    match_dpi: int,
    min_score: float,
    min_size: int,
    min_dimension: int,
    min_scale: float,
    max_scale: float,
    scale_steps: int,
    padding: float,
    max_page_width: int,
    trim_template: bool,
) -> tuple[list[Match], list[dict]]:
    images_dir = find_images_dir(mineru_output)
    images = list_images(images_dir, min_size=min_size, min_dimension=min_dimension)
    if not images:
        raise RuntimeError(f"No usable MinerU images found in {images_dir}")

    doc = fitz.open(pdf_path)
    page_numbers = parse_pages(pages, len(doc))
    rendered_pages = {page: render_page(doc, page, match_dpi) for page in page_numbers}

    matches: list[Match] = []
    failures: list[dict] = []

    for image_path in images:
        with Image.open(image_path) as raw:
            template = raw.convert("RGB")
        if trim_template:
            template = trim_white_margin(template)

        best: Match | None = None
        for page_num, page_img in rendered_pages.items():
            score, pixel_box, scaled_size = match_template_on_page(
                template,
                page_img,
                min_scale=min_scale,
                max_scale=max_scale,
                scale_steps=scale_steps,
                max_page_width=max_page_width,
            )
            box = normalized_box(pixel_box, page_img.size, padding)
            candidate = Match(
                source=image_path,
                page=page_num,
                score=score,
                box=box,
                pixel_box=pixel_box,
                scaled_size=scaled_size,
            )
            if best is None or candidate.score > best.score:
                best = candidate

        if best and best.score >= min_score:
            matches.append(best)
            print(f"match {image_path.name}: page {best.page}, score {best.score:.3f}")
        else:
            failures.append({
                "source_image": str(image_path),
                "best_score": None if best is None else round(best.score, 4),
            })
            score_text = "none" if best is None else f"{best.score:.3f}"
            print(f"skip  {image_path.name}: best score {score_text}")

    doc.close()
    matches.sort(key=lambda item: (item.page, item.pixel_box[1], item.pixel_box[0], item.source.name))
    return matches, failures


def write_regions(matches: Iterable[Match], output_file: Path, prefix: str) -> list[dict]:
    regions = []
    for idx, match in enumerate(matches, start=1):
        regions.append({
            "page": match.page,
            "name": f"{prefix}{idx}",
            "box": [round(v, 6) for v in match.box],
            "caption": False,
            "source_image": match.source.name,
            "match_score": round(match.score, 4),
        })

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(regions, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return regions


def dpi_for_region(
    page: fitz.Page,
    box: list[float],
    fallback_dpi: int,
    target_long_edge: int | None,
    min_dpi: int,
    max_dpi: int,
) -> int:
    if not target_long_edge:
        return fallback_dpi

    page_rect = page.rect
    rect_width = max((box[2] - box[0]) * page_rect.width, 1.0)
    rect_height = max((box[3] - box[1]) * page_rect.height, 1.0)
    long_edge_points = max(rect_width, rect_height)
    dpi = int(round(target_long_edge * 72.0 / long_edge_points))
    return max(min_dpi, min(max_dpi, dpi))


def crop_regions(
    pdf_path: Path,
    regions: list[dict],
    output_dir: Path,
    dpi: int,
    target_long_edge: int | None = None,
    min_dpi: int = 220,
    max_dpi: int = 900,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)

    for region in regions:
        page_num = int(region["page"])
        page = doc[page_num - 1]
        region_dpi = dpi_for_region(page, region["box"], dpi, target_long_edge, min_dpi, max_dpi)
        zoom = region_dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        x0, y0, x1, y1 = region["box"]
        crop_box = (
            int(round(x0 * img.width)),
            int(round(y0 * img.height)),
            int(round(x1 * img.width)),
            int(round(y1 * img.height)),
        )
        cropped = img.crop(crop_box)
        out = output_dir / f"p{page_num:03d}_{region['name']}.png"
        cropped.save(out, "PNG", optimize=True)
        print(f"crop  {out.name}: {cropped.width}x{cropped.height} ({region_dpi} DPI)")

    doc.close()


def write_debug_pages(pdf_path: Path, regions: list[dict], output_dir: Path, dpi: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = sorted({int(region["page"]) for region in regions})

    for page_num in pages:
        image = render_page(doc, page_num, dpi)
        draw = ImageDraw.Draw(image)
        for region in [r for r in regions if int(r["page"]) == page_num]:
            x0, y0, x1, y1 = region["box"]
            rect = (
                int(x0 * image.width),
                int(y0 * image.height),
                int(x1 * image.width),
                int(y1 * image.height),
            )
            draw.rectangle(rect, outline=(255, 0, 0), width=4)
            draw.text((rect[0] + 6, rect[1] + 6), region["name"], fill=(255, 0, 0))
        image.save(output_dir / f"debug_p{page_num:03d}.jpg", "JPEG", quality=90)

    doc.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Locate MinerU figures on PDF pages and crop high-DPI rendered figures."
    )
    parser.add_argument("pdf", type=Path, help="Input PDF")
    parser.add_argument("mineru_output", type=Path, help="MinerU output dir or images dir")
    parser.add_argument("--out", type=Path, default=Path("figures_mineru_assisted"), help="Output crop directory")
    parser.add_argument("--regions", type=Path, default=Path("regions_mineru.json"), help="Output regions JSON")
    parser.add_argument("--failures", type=Path, default=None, help="Optional unmatched images JSON")
    parser.add_argument("--pages", default="all", help='Pages to search, e.g. "all", "2-8", "1,3,5"')
    parser.add_argument("--match-dpi", type=int, default=150, help="DPI for matching pages")
    parser.add_argument("--crop-dpi", type=int, default=600, help="DPI for final crops when no target long edge is set")
    parser.add_argument("--target-long-edge", type=int, default=None,
                        help="Render each crop so its longest edge is near this pixel count, e.g. 4096 for 4K")
    parser.add_argument("--min-crop-dpi", type=int, default=220,
                        help="Minimum DPI when using --target-long-edge")
    parser.add_argument("--max-crop-dpi", type=int, default=900,
                        help="Maximum DPI when using --target-long-edge")
    parser.add_argument("--min-score", type=float, default=0.55, help="Minimum template match score")
    parser.add_argument("--min-size", type=int, default=10000, help="Minimum MinerU image file size")
    parser.add_argument("--min-dimension", type=int, default=160, help="Minimum MinerU image width/height")
    parser.add_argument("--min-scale", type=float, default=0.25, help="Smallest template scale to try")
    parser.add_argument("--max-scale", type=float, default=2.5, help="Largest template scale to try")
    parser.add_argument("--scale-steps", type=int, default=24, help="Number of scales to try")
    parser.add_argument("--padding", type=float, default=0.015, help="Padding as fraction of matched box size")
    parser.add_argument("--prefix", default="fig", help="Output region name prefix")
    parser.add_argument("--max-page-width", type=int, default=1400, help="Downsample page width for faster matching")
    parser.add_argument("--no-trim-template", action="store_true", help="Keep MinerU image margins during matching")
    parser.add_argument("--debug-dir", type=Path, default=None, help="Write preview pages with matched boxes")
    parser.add_argument("--regions-only", action="store_true", help="Only write regions JSON; do not crop")
    parser.add_argument("--copy-mineru", type=Path, default=None, help="Optional directory to copy matched MinerU source images")

    args = parser.parse_args()

    matches, failures = locate_mineru_images(
        pdf_path=args.pdf,
        mineru_output=args.mineru_output,
        pages=args.pages,
        match_dpi=args.match_dpi,
        min_score=args.min_score,
        min_size=args.min_size,
        min_dimension=args.min_dimension,
        min_scale=args.min_scale,
        max_scale=args.max_scale,
        scale_steps=args.scale_steps,
        padding=args.padding,
        max_page_width=args.max_page_width,
        trim_template=not args.no_trim_template,
    )

    regions = write_regions(matches, args.regions, args.prefix)
    print(f"wrote {len(regions)} regions to {args.regions}")

    if args.failures:
        args.failures.parent.mkdir(parents=True, exist_ok=True)
        with open(args.failures, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2, ensure_ascii=False)
            f.write("\n")

    if args.copy_mineru:
        args.copy_mineru.mkdir(parents=True, exist_ok=True)
        for match in matches:
            shutil.copy2(match.source, args.copy_mineru / match.source.name)

    if args.debug_dir:
        write_debug_pages(args.pdf, regions, args.debug_dir, args.match_dpi)
        print(f"wrote debug previews to {args.debug_dir}")

    if not args.regions_only:
        crop_regions(
            args.pdf,
            regions,
            args.out,
            args.crop_dpi,
            args.target_long_edge,
            args.min_crop_dpi,
            args.max_crop_dpi,
        )
        print(f"done: saved {len(regions)} crops to {args.out}")


if __name__ == "__main__":
    main()
