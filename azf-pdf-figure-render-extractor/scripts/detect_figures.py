#!/usr/bin/env python3
"""
Smart figure detection that distinguishes between text blocks and actual figures.

Usage:
    python detect_figures.py preview_dir --out regions.json --visualize
"""

import sys
import argparse
from pathlib import Path
import json

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install opencv-python pillow numpy")
    sys.exit(1)


def detect_figure_regions(image_path, min_area_ratio=0.05, visualize=False):
    """
    Detect figure regions by looking for large non-text blocks.

    Strategy:
    1. Convert to grayscale
    2. Find large connected regions of non-white pixels
    3. Filter by size, aspect ratio, and position
    4. Exclude text-heavy regions (high edge density)
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    # Threshold to find non-white regions
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Morphological operations to connect nearby regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    page_area = width * height
    min_area = page_area * min_area_ratio

    candidates = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h

        # Filter 1: Minimum area
        if area < min_area:
            continue

        # Filter 2: Aspect ratio (avoid very thin regions like lines)
        aspect = max(w, h) / min(w, h)
        if aspect > 8:
            continue

        # Filter 3: Position (figures usually not at very top)
        if y < height * 0.05:  # Skip top 5% (headers)
            continue

        # Filter 4: Check if region looks like a figure vs text
        # Figures have more uniform blocks, text has many small edges
        roi = binary[y:y+h, x:x+w]
        edge_density = np.sum(roi > 0) / (w * h)

        # Text regions have lower fill density (more white space between lines)
        # Figures have higher fill density (more continuous content)
        if edge_density < 0.15:  # Too sparse, likely text
            continue

        candidates.append({
            'box': (x, y, x + w, y + h),
            'area': area,
            'edge_density': edge_density,
            'y_pos': y / height
        })

    # Sort by y position (top to bottom)
    candidates.sort(key=lambda c: c['y_pos'])

    # Normalize coordinates
    regions = []
    for idx, candidate in enumerate(candidates, start=1):
        x0, y0, x1, y1 = candidate['box']
        regions.append({
            'name': f'fig{idx}',
            'box': [x0 / width, y0 / height, x1 / width, y1 / height],
            'area_ratio': candidate['area'] / page_area,
            'edge_density': candidate['edge_density']
        })

    # Visualize if requested
    if visualize and regions:
        vis_img = img.copy()
        for region in regions:
            x0 = int(region['box'][0] * width)
            y0 = int(region['box'][1] * height)
            x1 = int(region['box'][2] * width)
            y1 = int(region['box'][3] * height)

            cv2.rectangle(vis_img, (x0, y0), (x1, y1), (0, 0, 255), 3)
            cv2.putText(vis_img, region['name'], (x0 + 10, y0 + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        vis_path = image_path.parent / f"{image_path.stem}_detected.jpg"
        cv2.imwrite(str(vis_path), vis_img)
        print(f"  Visualization saved: {vis_path.name}")

    return regions


def main():
    parser = argparse.ArgumentParser(
        description="Smart figure detection for academic PDFs"
    )
    parser.add_argument("preview_dir", type=Path, help="Directory with rendered pages")
    parser.add_argument("--out", type=Path, default=Path("regions_detected.json"),
                       help="Output JSON file")
    parser.add_argument("--min-area", type=float, default=0.05,
                       help="Minimum area ratio (default: 0.05)")
    parser.add_argument("--visualize", action="store_true",
                       help="Save visualization images")

    args = parser.parse_args()

    if not args.preview_dir.exists():
        print(f"Error: Directory not found: {args.preview_dir}")
        sys.exit(1)

    page_files = sorted(args.preview_dir.glob("*.png"))

    if not page_files:
        print(f"No PNG files found in {args.preview_dir}")
        sys.exit(1)

    print(f"Detecting figures in {len(page_files)} pages...")
    print(f"Min area ratio: {args.min_area}")
    print()

    all_regions = []

    for page_file in page_files:
        # Extract page number
        page_num = int(page_file.stem.split("-")[-1])

        print(f"Page {page_num}: {page_file.name}")

        regions = detect_figure_regions(page_file, args.min_area, args.visualize)

        # Add page number to each region
        for region in regions:
            region['page'] = page_num
            region['caption'] = False

        all_regions.extend(regions)
        print(f"  Found {len(regions)} figure(s)")
        for region in regions:
            print(f"    {region['name']}: area={region['area_ratio']:.2%}, "
                  f"density={region['edge_density']:.2f}")

    # Save to JSON
    # Remove debug fields
    for region in all_regions:
        region.pop('area_ratio', None)
        region.pop('edge_density', None)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(all_regions, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(all_regions)} regions to {args.out}")
    print("\nPlease review the detected regions and adjust if needed.")


if __name__ == "__main__":
    main()
