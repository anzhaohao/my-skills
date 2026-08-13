#!/usr/bin/env python3
"""
Collect and organize figures from MinerU PDF-to-Markdown output.

This is useful when the user wants MinerU's own extracted images instead of
PDF-rendered crops.

Usage:
    python collect_mineru_figures.py mineru_output_dir --out figures --exclude-small
"""

import argparse
import shutil
from pathlib import Path

from PIL import Image


def find_images_dir(mineru_output: Path) -> Path | None:
    candidates = [
        mineru_output,
        mineru_output / "images",
        mineru_output / "auto" / "images",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            image_files = list(candidate.glob("*.png")) + list(candidate.glob("*.jpg")) + list(candidate.glob("*.jpeg"))
            if image_files:
                return candidate

    return None


def collect_figures(
    mineru_output: Path,
    output_dir: Path,
    min_size: int = 10000,
    min_dimension: int = 200,
    exclude_small: bool = False,
    prefix: str | None = None,
    start_num: int = 1,
    copy_files: bool = True,
    allowed_formats: list[str] | None = None,
) -> None:
    if allowed_formats is None:
        allowed_formats = ["png", "jpg", "jpeg", "webp"]

    images_dir = find_images_dir(mineru_output)
    if images_dir is None:
        print(f"Error: no MinerU images found under {mineru_output}")
        print("Expected image files directly inside the path, images/, or auto/images/.")
        return

    image_files: list[Path] = []
    for ext in allowed_formats:
        image_files.extend(images_dir.glob(f"*.{ext}"))
        image_files.extend(images_dir.glob(f"*.{ext.upper()}"))
    image_files = sorted(set(image_files))

    output_dir.mkdir(parents=True, exist_ok=True)

    collected = []
    skipped = []

    for img_file in image_files:
        file_size = img_file.stat().st_size
        if exclude_small and file_size < min_size:
            skipped.append((img_file.name, f"file size {file_size} < {min_size}"))
            continue

        try:
            with Image.open(img_file) as img:
                width, height = img.size
        except Exception as exc:
            skipped.append((img_file.name, f"cannot read: {exc}"))
            continue

        if exclude_small and (width < min_dimension or height < min_dimension):
            skipped.append((img_file.name, f"dimension {width}x{height} too small"))
            continue

        output_name = f"{prefix}{start_num + len(collected)}{img_file.suffix}" if prefix else img_file.name
        output_file = output_dir / output_name

        if copy_files:
            shutil.copy2(img_file, output_file)
        else:
            shutil.move(str(img_file), str(output_file))

        collected.append((img_file.name, output_name, width, height, file_size))
        print(f"collect {img_file.name} -> {output_name} ({width}x{height}, {file_size // 1024}KB)")

    print(f"done: collected {len(collected)} figures to {output_dir}")

    if skipped:
        print(f"skipped {len(skipped)} files")
        for name, reason in skipped[:10]:
            print(f"skip {name}: {reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect and organize figures from MinerU output")
    parser.add_argument("mineru_output", type=Path, help="MinerU output directory or images directory")
    parser.add_argument("--out", type=Path, default=Path("figures"), help="Output directory")
    parser.add_argument("--min-size", type=int, default=10000, help="Minimum file size in bytes")
    parser.add_argument("--min-dimension", type=int, default=200, help="Minimum width/height in pixels")
    parser.add_argument("--exclude-small", action="store_true", help="Exclude images smaller than thresholds")
    parser.add_argument("--prefix", type=str, default=None, help="Rename with prefix, e.g. fig -> fig1.png")
    parser.add_argument("--start-num", type=int, default=1, help="Starting number for renaming")
    parser.add_argument("--move", action="store_true", help="Move files instead of copying them")
    parser.add_argument("--formats", type=str, default="png,jpg,jpeg,webp", help="Allowed formats")

    args = parser.parse_args()
    collect_figures(
        mineru_output=args.mineru_output,
        output_dir=args.out,
        min_size=args.min_size,
        min_dimension=args.min_dimension,
        exclude_small=args.exclude_small,
        prefix=args.prefix,
        start_num=args.start_num,
        copy_files=not args.move,
        allowed_formats=[item.strip() for item in args.formats.split(",") if item.strip()],
    )


if __name__ == "__main__":
    main()
