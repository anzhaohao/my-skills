---
name: pdf-figure-render-extractor
description: Extract clean high-resolution figures/images from academic PDFs for PPT, Obsidian notes, paper reading, or image collection. Use when Codex needs to use MinerU output to locate figures, run local Docker MinerU, crop high-DPI rendered PDF pages, collect MinerU images, manually crop PDF regions, or handle PDFs where direct image extraction produces fragmented masks, alpha layers, separated color layers, vector overlays, or incomplete images.
---

# PDF Figure Render Extractor

## Purpose

Extract visually complete figures from academic PDFs. Prefer MinerU-assisted positioning when MinerU output is available, then crop the final visible figure from a high-DPI PDF page render.

Use rendering-first extraction when direct PDF image extraction produces fragmented masks, alpha layers, color layers, vector overlays, or incomplete images. Do not present rendered crops as original embedded source images; describe them as high-resolution visual reconstruction from the PDF page.

## Core Principle

Preferred workflow:

```text
MinerU figure image -> locate same visual area on rendered PDF page -> regions.json -> high-DPI crop
```

Fallback workflow:

```text
PDF page render -> manual/auto region selection -> high-DPI crop
```

Avoid using direct internal image extraction as the primary method for scientific figures unless the user explicitly asks for raw embedded objects.

## Default Quality

- `preview`: target long edge about 1600 px, for quick checks
- `normal`: target long edge about 2560 px
- `4k`: target long edge about 4096 px, default
- `8k`: target long edge about 8192 px, large files
- `dpi`: fixed-DPI mode using `--crop-dpi`

Default recommendation: `--clarity 4k`. It chooses crop DPI per region so each output figure's longest edge is near 4096 pixels, bounded by `--min-crop-dpi` and `--max-crop-dpi`.

## Required Workflow

1. Inspect the PDF and the user's output needs.
2. Use Mode 0 when local Docker MinerU is available.
3. Use existing MinerU output before rerunning conversion.
4. Use MinerU-assisted crop before manual JSON cropping when MinerU images exist.
5. Create debug previews or a contact sheet for visual review.
6. Save final crops as PNG by default.
7. Verify that labels, axes, legends, colorbars, and subfigure letters are complete.

## Mode 0: Current Docker MinerU

Use this as the default with the local `mineru:latest` image. The current local deployment uses MinerU 3.x, so use `mineru -p {pdf} -o {out}` rather than the old `magic-pdf` command.

```bash
python scripts/extract_pdf_figures.py input.pdf \
  --mode docker-run \
  --docker-image mineru:latest \
  --out-root output \
  --clarity 4k \
  --yes
```

`docker-run` starts a one-off container, mounts the PDF directory at `/data/input`, mounts the MinerU output at `/data/output`, runs `mineru -p /data/input/<file>.pdf -o /data/output`, then removes the container. It does not require the Gradio/API Compose services to be running.

Ask the user before starting MinerU unless they explicitly approved conversion in the same request. Use `--yes` only after that approval. If Docker Desktop is stopped, start it first.

If the Docker host should not expose GPUs, add:

```bash
--docker-gpus none
```

For a running Compose container instead of a one-off container, use `--mode docker`. In the current local setup the container name is `mineru-gradio`; it must be running before `docker exec` can work.

```bash
python scripts/extract_pdf_figures.py input.pdf \
  --mode docker \
  --container mineru-gradio \
  --mineru-command "mineru -p {pdf} -o {out}" \
  --out-root output \
  --yes
```

Override `--mineru-command` only when the image/container exposes a different command. Keep `{pdf}` and `{out}` placeholders; the script shell-quotes them.

## Existing MinerU Output

Use this when Gradio/API or another MinerU run has already produced images.

For a precise image folder:

```bash
python scripts/extract_pdf_figures.py input.pdf \
  --mode existing \
  --mineru-output "\\?\E:\software\DockerProject\MinerU\output\gradio\...\hybrid_auto\images" \
  --out-root output
```

For a Gradio run folder:

```bash
python scripts/extract_pdf_figures.py input.pdf \
  --mode latest-gradio \
  --mineru-output-root "\\?\E:\software\DockerProject\MinerU\output\gradio\<PDF-or-task-folder>" \
  --out-root output
```

The script searches for `hybrid_auto/images`, `auto/images`, or `images`, copies usable MinerU images into `output/<pdf-stem>/02_figures/mineru_images/`, then uses them for high-DPI crops.

Use `--copy-only` when dependencies for high-DPI cropping are missing or the user only wants MinerU images copied. Use `--force-mineru` only when the user wants to ignore existing images and rerun conversion. Use `--timestamped` only when the user wants a fresh output folder.

## Direct Crop Modes

Render pages for manual inspection:

```bash
python scripts/render_pages.py input.pdf --out out_pages --dpi 450 --pages all
```

Crop known regions from JSON:

```bash
python scripts/crop_regions.py input.pdf --regions regions.json --out figures --dpi 450
```

Run semi-auto detection:

```bash
python scripts/auto_crop_figures.py input.pdf --out figures_auto --dpi 450 --min-area 0.03
```

Auto mode is allowed, but warn that complex layouts may require manual correction.

Run MinerU-assisted crop directly:

```bash
python scripts/mineru_assisted_crop.py input.pdf mineru_output_dir \
  --out figures \
  --regions regions_mineru.json \
  --pages all \
  --match-dpi 200 \
  --target-long-edge 4096 \
  --debug-dir debug_matches
```

Review `debug_matches/` before trusting final crops. If matches are wrong, raise `--min-score`, restrict `--pages`, or reduce the scale range. If matches are missed, lower `--min-score`, increase `--scale-steps`, or try `--no-trim-template`.

Collect MinerU's own image files without re-cropping:

```bash
python scripts/collect_mineru_figures.py mineru_output_dir \
  --out figures_mineru \
  --prefix fig \
  --exclude-small
```

This copies by default. Use `--move` only when the user explicitly wants to move files.

## Output

Use clear file names:

```text
<pdf_stem>_p001_fig01.png
<pdf_stem>_p001_fig02.png
<pdf_stem>_p002_fig01.png
```

For Obsidian-friendly output, also create or preserve:

```text
figures/
figures_webp/
contact_sheet.jpg
```

The one-command script writes `figure_extraction_manifest.json` with paths, mode, clarity, and crop status.

## Quality Rules

- Use PNG for maximum clarity.
- Use WebP only as an optional compressed copy.
- Default to 4K target long edge for PPT and notes.
- Use `--clarity 8k` only when the user needs extreme detail.
- Use `--clarity dpi --crop-dpi <value>` when the user explicitly asks for a fixed DPI.
- Do not upscale raster images after cropping; increase render clarity instead.
- Use a white background unless transparency is required.
- Trim obvious page margins, but do not crop labels, axes, legends, colorbars, scale bars, or subfigure labels such as `(a)`, `(b)`, `(c)`.
- Include captions only when the user asks for caption preservation.
- If the user says "只要纯图片不要说明" or "no captions", exclude captions.

## Dependencies

Python packages:

```bash
pip install pymupdf pillow opencv-python numpy
```

PyMuPDF renders PDF pages. Pillow handles images. OpenCV and NumPy support automatic detection and MinerU-assisted template matching.

## Failure Handling

If direct crop is wrong:

1. Increase DPI or target long edge.
2. Render full page.
3. Make a contact sheet.
4. Identify boxes visually.
5. Re-crop with JSON regions.

If auto-crop merges multiple figures, split the region manually in JSON.

If auto-crop misses faint lines or labels, lower thresholds, use manual crop, or increase DPI.

If output looks blurry, use `--clarity 4k` or `--clarity 8k`, avoid WebP compression, and save PNG.

## Manual Region JSON

Use 1-based page numbers. Coordinates are normalized relative to the rendered page:

```json
[
  {
    "page": 1,
    "name": "fig1",
    "box": [0.08, 0.12, 0.92, 0.78],
    "caption": false
  }
]
```

Box format: `[x0, y0, x1, y1]`, where `x0/y0` are left/top and `x1/y1` are right/bottom.
