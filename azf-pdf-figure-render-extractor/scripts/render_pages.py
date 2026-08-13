#!/usr/bin/env python3
"""
Render PDF pages to high-resolution PNG images.

Usage:
    python render_pages.py input.pdf --out out_pages --dpi 450 --pages all
    python render_pages.py input.pdf --out out_pages --dpi 600 --pages 1,3,5-7
"""

import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Install with: pip install pymupdf")
    sys.exit(1)


def parse_page_spec(spec: str, total_pages: int) -> list[int]:
    """
    Parse page specification string.

    Examples:
        "all" -> [1, 2, 3, ..., total_pages]
        "1,3,5" -> [1, 3, 5]
        "1-5" -> [1, 2, 3, 4, 5]
        "1,3-5,7" -> [1, 3, 4, 5, 7]

    Returns 0-based page indices.
    """
    if spec.lower() == "all":
        return list(range(total_pages))

    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start = int(start.strip())
            end = int(end.strip())
            pages.update(range(start - 1, end))  # Convert to 0-based
        else:
            pages.add(int(part) - 1)  # Convert to 0-based

    return sorted(pages)


def render_pages(pdf_path: Path, output_dir: Path, dpi: int = 450, pages: str = "all"):
    """
    Render PDF pages to PNG at specified DPI.

    Args:
        pdf_path: Path to input PDF
        output_dir: Directory to save rendered pages
        dpi: Resolution in dots per inch
        pages: Page specification ("all", "1,3,5", "1-5", etc.)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    page_indices = parse_page_spec(pages, total_pages)

    pdf_stem = pdf_path.stem
    zoom = dpi / 72  # PDF default is 72 DPI
    mat = fitz.Matrix(zoom, zoom)

    print(f"Rendering {len(page_indices)} pages at {dpi} DPI...")

    for page_idx in page_indices:
        if page_idx >= total_pages:
            print(f"Warning: Page {page_idx + 1} does not exist (total: {total_pages})")
            continue

        page = doc[page_idx]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        output_file = output_dir / f"{pdf_stem}_p{page_idx + 1:03d}.png"
        pix.save(str(output_file))

        print(f"  ✓ Page {page_idx + 1} -> {output_file.name} ({pix.width}x{pix.height})")

    doc.close()
    print(f"\nDone: {len(page_indices)} pages rendered to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Render PDF pages to high-resolution PNG images"
    )
    parser.add_argument("pdf", type=Path, help="Input PDF file")
    parser.add_argument("--out", type=Path, default=Path("out_pages"),
                        help="Output directory (default: out_pages)")
    parser.add_argument("--dpi", type=int, default=450,
                        help="Resolution in DPI (default: 450)")
    parser.add_argument("--pages", type=str, default="all",
                        help='Pages to render: "all", "1,3,5", "1-5", etc. (default: all)')

    args = parser.parse_args()

    render_pages(args.pdf, args.out, args.dpi, args.pages)


if __name__ == "__main__":
    main()
