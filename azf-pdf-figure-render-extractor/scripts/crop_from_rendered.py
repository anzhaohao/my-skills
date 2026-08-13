#!/usr/bin/env python3
"""
Crop figures from pre-rendered PNG pages using JSON coordinates.
This is a simplified version that works without PyMuPDF.
"""

import json
import sys
from pathlib import Path
from PIL import Image


def crop_from_rendered_pages(pages_dir: Path, regions_file: Path, output_dir: Path):
    """Crop figures from already-rendered PNG pages."""

    with open(regions_file, "r", encoding="utf-8") as f:
        regions = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Cropping {len(regions)} regions from rendered pages...")

    for region in regions:
        page_num = region["page"]
        name = region["name"]
        box = region["box"]  # [x0, y0, x1, y1] normalized

        # Find the rendered page file
        page_file = pages_dir / f"paper-{page_num:02d}.png"

        if not page_file.exists():
            print(f"Warning: Page {page_num} not found, skipping {name}")
            continue

        # Load image
        img = Image.open(page_file)

        # Calculate crop box in pixels
        x0 = int(box[0] * img.width)
        y0 = int(box[1] * img.height)
        x1 = int(box[2] * img.width)
        y1 = int(box[3] * img.height)

        # Crop
        cropped = img.crop((x0, y0, x1, y1))

        # Save
        output_file = output_dir / f"p{page_num:03d}_{name}.png"
        cropped.save(output_file, "PNG", optimize=True)

        print(f"  ✓ Page {page_num} [{name}] -> {output_file.name} ({cropped.width}x{cropped.height})")

    print(f"\nDone: {len(regions)} figures saved to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python crop_from_rendered.py pages_dir regions.json output_dir")
        sys.exit(1)

    pages_dir = Path(sys.argv[1])
    regions_file = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    crop_from_rendered_pages(pages_dir, regions_file, output_dir)
