#!/usr/bin/env python3
"""
Automatically detect and crop figure regions from PDF pages.

Usage:
    python auto_crop_figures.py input.pdf --out figures_auto --dpi 450 --min-area 0.03
"""

import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
    import cv2
    import numpy as np
    from PIL import Image
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install pymupdf opencv-python pillow numpy")
    sys.exit(1)


def detect_figure_regions(image_array, min_area_ratio=0.03):
    """
    Detect likely figure regions in a page image.

    Args:
        image_array: numpy array of the page image (RGB)
        min_area_ratio: Minimum area as fraction of page area

    Returns:
        List of bounding boxes [(x0, y0, x1, y1), ...]
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    # Apply threshold to find non-white regions
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Morphological operations to connect nearby regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    page_area = image_array.shape[0] * image_array.shape[1]
    min_area = page_area * min_area_ratio

    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h

        # Filter by area
        if area < min_area:
            continue

        # Filter by aspect ratio (avoid very thin regions)
        aspect = max(w, h) / min(w, h)
        if aspect > 10:
            continue

        boxes.append((x, y, x + w, y + h))

    return boxes


def auto_crop_figures(pdf_path: Path, output_dir: Path, dpi: int = 450, min_area: float = 0.03):
    """
    Automatically detect and crop figures from PDF pages.

    Args:
        pdf_path: Path to input PDF
        output_dir: Directory to save cropped figures
        dpi: Resolution in DPI
        min_area: Minimum area ratio for figure detection
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    pdf_stem = pdf_path.stem
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    print(f"Auto-detecting figures at {dpi} DPI (min_area={min_area})...")
    print("Warning: Auto-detection may merge multiple figures or miss faint content.")
    print("For precise results, use manual crop with regions.json.\n")

    total_figures = 0

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to numpy array
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

        # Detect regions
        boxes = detect_figure_regions(img_array, min_area)

        if not boxes:
            print(f"  Page {page_idx + 1}: No figures detected")
            continue

        # Convert to PIL Image for cropping
        img = Image.fromarray(img_array)

        for fig_idx, (x0, y0, x1, y1) in enumerate(boxes, start=1):
            cropped = img.crop((x0, y0, x1, y1))

            output_file = output_dir / f"{pdf_stem}_p{page_idx + 1:03d}_fig{fig_idx:02d}.png"
            cropped.save(output_file, "PNG", optimize=True)

            print(f"  ✓ Page {page_idx + 1} Fig {fig_idx} -> {output_file.name} ({cropped.width}x{cropped.height})")
            total_figures += 1

    doc.close()
    print(f"\nDone: {total_figures} figures auto-detected and saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Automatically detect and crop figure regions from PDF pages"
    )
    parser.add_argument("pdf", type=Path, help="Input PDF file")
    parser.add_argument("--out", type=Path, default=Path("figures_auto"),
                        help="Output directory (default: figures_auto)")
    parser.add_argument("--dpi", type=int, default=450,
                        help="Resolution in DPI (default: 450)")
    parser.add_argument("--min-area", type=float, default=0.03,
                        help="Minimum area ratio for detection (default: 0.03)")

    args = parser.parse_args()

    auto_crop_figures(args.pdf, args.out, args.dpi, args.min_area)


if __name__ == "__main__":
    main()
