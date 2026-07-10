#!/usr/bin/env python3
"""
Interactive figure region selector.

Usage:
    python select_regions.py preview_dir output_regions.json

Opens each page image and lets you visually select figure regions.
"""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import messagebox


class RegionSelector:
    def __init__(self, image_path, page_num):
        self.image_path = image_path
        self.page_num = page_num
        self.img = Image.open(image_path)
        self.regions = []

        # Scale image to fit screen if needed
        self.scale = 1.0
        max_width = 1400
        max_height = 900
        if self.img.width > max_width or self.img.height > max_height:
            scale_w = max_width / self.img.width
            scale_h = max_height / self.img.height
            self.scale = min(scale_w, scale_h)
            new_size = (int(self.img.width * self.scale), int(self.img.height * self.scale))
            self.display_img = self.img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            self.display_img = self.img.copy()

        self.root = tk.Tk()
        self.root.title(f"Select Figure Regions - Page {page_num}")

        self.canvas = tk.Canvas(self.root, width=self.display_img.width, height=self.display_img.height)
        self.canvas.pack()

        self.photo = tk.PhotoImage(data=self._pil_to_photoimage(self.display_img))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Instructions
        instructions = tk.Label(self.root, text="拖动鼠标框选图片区域。完成后关闭窗口。",
                               font=("Arial", 12), bg="yellow")
        instructions.pack()

    def _pil_to_photoimage(self, pil_img):
        """Convert PIL Image to PhotoImage."""
        import io
        bio = io.BytesIO()
        pil_img.save(bio, format="PNG")
        return bio.getvalue()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=3
        )

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.rect:
            x0 = min(self.start_x, event.x)
            y0 = min(self.start_y, event.y)
            x1 = max(self.start_x, event.x)
            y1 = max(self.start_y, event.y)

            # Convert to normalized coordinates (relative to original image)
            norm_x0 = (x0 / self.scale) / self.img.width
            norm_y0 = (y0 / self.scale) / self.img.height
            norm_x1 = (x1 / self.scale) / self.img.width
            norm_y1 = (y1 / self.scale) / self.img.height

            name = f"fig{len(self.regions) + 1}"

            self.regions.append({
                "page": self.page_num,
                "name": name,
                "box": [norm_x0, norm_y0, norm_x1, norm_y1],
                "caption": False
            })

            # Add label
            self.canvas.create_text(
                x0 + 5, y0 + 5,
                text=name,
                anchor=tk.NW,
                fill="red",
                font=("Arial", 14, "bold")
            )

            self.rect = None

    def run(self):
        self.root.mainloop()
        return self.regions


def main():
    if len(sys.argv) < 3:
        print("Usage: python select_regions.py preview_dir output_regions.json")
        sys.exit(1)

    preview_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not preview_dir.exists():
        print(f"Error: Directory not found: {preview_dir}")
        sys.exit(1)

    # Find all PNG files
    page_files = sorted(preview_dir.glob("*.png"))

    if not page_files:
        print(f"No PNG files found in {preview_dir}")
        sys.exit(1)

    print(f"Found {len(page_files)} pages")
    print("Instructions:")
    print("  1. 拖动鼠标框选图片区域")
    print("  2. 可以框选多个区域")
    print("  3. 完成后关闭窗口进入下一页")
    print()

    all_regions = []

    for page_file in page_files:
        # Extract page number from filename (e.g., paper-02.png -> 2)
        page_num = int(page_file.stem.split("-")[-1])

        print(f"Page {page_num}: {page_file.name}")

        selector = RegionSelector(page_file, page_num)
        regions = selector.run()

        all_regions.extend(regions)
        print(f"  Selected {len(regions)} regions")

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_regions, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(all_regions)} regions to {output_file}")


if __name__ == "__main__":
    main()
