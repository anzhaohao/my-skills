#!/usr/bin/env python3
"""
Crop figure regions from PDF pages based on JSON coordinates.

Usage:
    python crop_regions.py input.pdf --regions regions.json --out figures --dpi 600
"""

import sys
import argparse
import json
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install pymupdf pillow")
    sys.exit(1)


def crop_regions(pdf_path: Path, regions_file: Path, output_dir: Path, dpi: int = 450):
    """
    Crop figure regions from PDF pages.

    Args:
        pdf_path: Path to input PDF
        regions_file: Path to JSON file with crop regions
        output_dir: Directory to save cropped figures
        dpi: Resolution in DPI
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not regions_file.exists():
        raise FileNotFoundError(f"Regions file not found: {regions_file}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load regions
    with open(regions_file, "r", encoding="utf-8") as f:
        regions = json.load(f)

    doc = fitz.open(pdf_path)
    pdf_stem = pdf_path.stem
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    print(f"Cropping {len(regions)} regions at {dpi} DPI...")

    for region in regions:
        page_num = region["page"]  # 1-based
        name = region["name"]
        box = region["box"]  # [x0, y0, x1, y1] normalized 0-1
        include_caption = region.get("caption", False)

        page_idx = page_num - 1  # Convert to 0-based

        if page_idx >= len(doc):
            print(f"Warning: Page {page_num} does not exist, skipping {name}")
            continue

        # Render full page
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Calculate crop box in pixels
        x0 = int(box[0] * pix.width)
        y0 = int(box[1] * pix.height)
        x1 = int(box[2] * pix.width)
        y1 = int(box[3] * pix.height)

        # Crop
        cropped = img.crop((x0, y0, x1, y1))

        # Save
        output_file = output_dir / f"{pdf_stem}_p{page_num:03d}_{name}.png"
        cropped.save(output_file, "PNG", optimize=True)

        print(f"  ✓ Page {page_num} [{name}] -> {output_file.name} ({cropped.width}x{cropped.height})")

    doc.close()
    print(f"\nDone: {len(regions)} figures saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Crop figure regions from PDF pages based on JSON coordinates"
    )
    parser.add_argument("pdf", type=Path, help="Input PDF file")
    parser.add_argument("--regions", type=Path, required=True,
                        help="JSON file with crop regions")
    parser.add_argument("--out", type=Path, default=Path("figures"),
                        help="Output directory (default: figures)")
    parser.add_argument("--dpi", type=int, default=450,
                        help="Resolution in DPI (default: 450)")

    args = parser.parse_args()

    crop_regions(args.pdf, args.regions, args.out, args.dpi)


if __name__ == "__main__":
    main()
