from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import fitz

SKILL_ROOT = Path("C:/Users/anzhaofeng/.skills-manager/skills/pdf-figure-render-extractor")
EXTRACT_SCRIPT = SKILL_ROOT / "scripts" / "extract_pdf_figures.py"
CROP_REGIONS_SCRIPT = SKILL_ROOT / "scripts" / "crop_regions.py"


def render_page_previews(pdf_path: Path, image_dir: Path, max_pages: int = 3, dpi: int = 220) -> list[dict]:
    image_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    manifest: list[dict] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page_index in range(min(max_pages, len(doc))):
        page = doc[page_index]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        name = f"Page-{page_index + 1:02d}-preview.png"
        out_path = image_dir / name
        pix.save(out_path)
        manifest.append(
            {
                "asset_id": f"page-{page_index + 1:02d}-preview",
                "file_path": str(out_path),
                "source_pdf": str(pdf_path),
                "page": page_index + 1,
                "figure_label": f"Page {page_index + 1} preview",
                "crop_method": "full_page_preview",
                "clarity": f"{dpi}dpi",
                "crop_status": "needs_review",
                "accepted_as_highres_figure": False,
            }
        )
    return manifest


def write_figure_manifest(path: Path, manifest: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def figure_skill_status() -> dict:
    return {
        "skill_root": str(SKILL_ROOT),
        "available": EXTRACT_SCRIPT.exists(),
        "script": str(EXTRACT_SCRIPT),
        "manual_crop_script": str(CROP_REGIONS_SCRIPT),
    }


def run_pdf_figure_render_extractor(
    pdf_path: Path,
    out_root: Path,
    mode: str = "existing",
    mineru_output: Path | None = None,
    clarity: str = "4k",
    docker_image: str = "mineru:latest",
) -> subprocess.CompletedProcess:
    if not EXTRACT_SCRIPT.exists():
        raise FileNotFoundError(EXTRACT_SCRIPT)
    command = [
        sys.executable,
        str(EXTRACT_SCRIPT),
        "--mode",
        mode,
        "--out-root",
        str(out_root),
        "--project-name",
        pdf_path.stem,
        "--clarity",
        clarity,
        "--docker-image",
        docker_image,
        "--yes",
        str(pdf_path),
    ]
    if mineru_output:
        command.extend(["--mineru-output", str(mineru_output)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def run_manual_region_crop(pdf_path: Path, regions_path: Path, output_dir: Path, dpi: int = 450) -> subprocess.CompletedProcess:
    if not CROP_REGIONS_SCRIPT.exists():
        raise FileNotFoundError(CROP_REGIONS_SCRIPT)
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(CROP_REGIONS_SCRIPT),
        str(pdf_path),
        "--regions",
        str(regions_path),
        "--out",
        str(output_dir),
        "--dpi",
        str(dpi),
    ]
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def manual_region_manifest(pdf_path: Path, regions_path: Path, output_dir: Path, dpi: int = 450) -> list[dict]:
    regions = json.loads(regions_path.read_text(encoding="utf-8-sig"))
    manifest: list[dict] = []
    for index, region in enumerate(regions, start=1):
        page = int(region["page"])
        name = str(region["name"])
        file_path = output_dir / f"{pdf_path.stem}_p{page:03d}_{name}.png"
        label_match = re.search(r"(?:fig|figure)[-_ ]?(\d+)", name, re.IGNORECASE)
        table_match = re.search(r"table[-_ ]?(\d+)", name, re.IGNORECASE)
        if label_match:
            label = f"Fig {label_match.group(1)}"
            source_type = "figure"
        elif table_match:
            label = f"Table {table_match.group(1)}"
            source_type = "table"
        else:
            label = f"Figure/Table {index}"
            source_type = "figure"
        manifest.append(
            {
                "asset_id": f"manual-{source_type}-{index:02d}-p{page:03d}",
                "file_path": str(file_path.resolve()),
                "source_pdf": str(pdf_path.resolve()),
                "page": page,
                "figure_label": label,
                "source_type": source_type,
                "crop_method": "manual_pdf_render",
                "clarity": f"{dpi}dpi",
                "crop_status": "success" if file_path.is_file() else "failed",
                "accepted_as_highres_figure": file_path.is_file(),
                "region": region.get("box"),
            }
        )
    return manifest