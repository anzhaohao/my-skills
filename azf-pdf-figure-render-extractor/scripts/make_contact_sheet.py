#!/usr/bin/env python3
"""
Create a contact sheet (grid preview) of rendered pages or cropped figures.

Usage:
    python make_contact_sheet.py input_dir --out contact_sheet.jpg --cols 3
"""

import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Install with: pip install pillow")
    sys.exit(1)


def make_contact_sheet(input_dir: Path, output_file: Path, cols: int = 3, thumb_size: int = 400):
    """
    Create a contact sheet from images in a directory.

    Args:
        input_dir: Directory containing images
        output_file: Output contact sheet file
        cols: Number of columns
        thumb_size: Thumbnail size (max dimension)
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Find all images
    image_files = sorted(input_dir.glob("*.png")) + sorted(input_dir.glob("*.jpg"))

    if not image_files:
        print(f"No images found in {input_dir}")
        return

    print(f"Creating contact sheet from {len(image_files)} images...")

    # Load and resize images
    thumbnails = []
    for img_file in image_files:
        img = Image.open(img_file)
        img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        thumbnails.append((img, img_file.name))

    # Calculate grid dimensions
    rows = (len(thumbnails) + cols - 1) // cols

    # Calculate canvas size
    max_width = max(img.width for img, _ in thumbnails)
    max_height = max(img.height for img, _ in thumbnails)

    canvas_width = cols * max_width + (cols + 1) * 20  # 20px padding
    canvas_height = rows * (max_height + 40) + (rows + 1) * 20  # 40px for label

    # Create canvas
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")

    # Paste thumbnails
    for idx, (img, name) in enumerate(thumbnails):
        row = idx // cols
        col = idx % cols

        x = col * max_width + (col + 1) * 20
        y = row * (max_height + 40) + (row + 1) * 20

        # Center image in cell
        x_offset = (max_width - img.width) // 2
        y_offset = (max_height - img.height) // 2

        canvas.paste(img, (x + x_offset, y + y_offset))

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_file, "JPEG", quality=90, optimize=True)

    print(f"✓ Contact sheet saved: {output_file}")
    print(f"  Grid: {rows} rows × {cols} cols")
    print(f"  Size: {canvas_width}×{canvas_height}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a contact sheet (grid preview) from images"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing images")
    parser.add_argument("--out", type=Path, default=Path("contact_sheet.jpg"),
                        help="Output file (default: contact_sheet.jpg)")
    parser.add_argument("--cols", type=int, default=3,
                        help="Number of columns (default: 3)")
    parser.add_argument("--thumb-size", type=int, default=400,
                        help="Thumbnail max dimension (default: 400)")

    args = parser.parse_args()

    make_contact_sheet(args.input_dir, args.out, args.cols, args.thumb_size)


if __name__ == "__main__":
    main()
