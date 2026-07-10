from __future__ import annotations

from pathlib import Path

from workflow.adapters.figure_render_extractor import render_page_previews, write_figure_manifest


def create_preview_figure_assets(pdf_path: Path, image_dir: Path, manifest_path: Path, max_pages: int = 3) -> list[dict]:
    manifest = render_page_previews(pdf_path, image_dir, max_pages=max_pages)
    write_figure_manifest(manifest_path, manifest)
    return manifest

