#!/usr/bin/env python3
"""
One-command PDF figure extraction workflow.

It can run MinerU in a one-off Docker container or inside an existing Docker
container, discover MinerU's hybrid_auto/images output, copy those images into
the project output folder, and optionally use them to crop high-DPI
PDF-rendered figures.

Typical use with the current local MinerU image:
    python extract_pdf_figures.py paper.pdf --mode docker-run --docker-image mineru:latest --yes

For an already running MinerU container:
    python extract_pdf_figures.py paper.pdf --mode docker --container mineru-gradio --yes

For an existing Gradio output tree:
    python extract_pdf_figures.py paper.pdf --mode latest-gradio ^
      --mineru-output-root "\\\\?\\E:\\software\\DockerProject\\MinerU\\output\\gradio\\<pdf-folder>"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
CLARITY_PRESETS = {
    "preview": {"target_long_edge": 1600, "match_dpi": 120},
    "normal": {"target_long_edge": 2560, "match_dpi": 150},
    "4k": {"target_long_edge": 4096, "match_dpi": 200},
    "8k": {"target_long_edge": 8192, "match_dpi": 240},
    "dpi": {"target_long_edge": None, "match_dpi": None},
}


def normalize_windows_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    return Path(path_text)


def docker_mount_path(path: Path) -> str:
    text = str(path.resolve())
    if text.startswith("\\\\?\\"):
        text = text[4:]
    return text.replace("\\", "/")


def slugify(text: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^\w.-]+", "_", text, flags=re.UNICODE).strip("_.-")
    return cleaned[:max_len] or "paper"


def comparable_text(text: str) -> str:
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE).lower()


def run_command(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print("run:", " ".join(cmd))
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
    return result


def candidate_image_dirs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    if root.is_dir() and any(p.is_file() and p.suffix.lower() in IMAGE_EXTS for p in root.iterdir()):
        candidates.append(root)

    patterns = [
        "**/hybrid_auto/images",
        "**/auto/images",
        "**/images",
    ]
    for pattern in patterns:
        candidates.extend(path for path in root.glob(pattern) if path.is_dir())

    unique = []
    seen = set()
    for path in candidates:
        key = str(path.resolve())
        if key not in seen and any(p.is_file() and p.suffix.lower() in IMAGE_EXTS for p in path.iterdir()):
            seen.add(key)
            unique.append(path)
    return unique


def find_best_images_dir(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"MinerU output root not found: {root}")
    candidates = candidate_image_dirs(root)
    if not candidates:
        raise FileNotFoundError(f"No MinerU images directory found under: {root}")

    def score(path: Path) -> tuple[int, float]:
        text = str(path).replace("\\", "/")
        priority = 0
        if text.endswith("/hybrid_auto/images"):
            priority = 3
        elif text.endswith("/auto/images"):
            priority = 2
        elif text.endswith("/images"):
            priority = 1
        latest_file_time = max((p.stat().st_mtime for p in path.iterdir() if p.is_file()), default=0)
        return priority, latest_file_time

    return max(candidates, key=score)


def find_latest_gradio_images(output_root: Path) -> Path:
    if not output_root.exists():
        raise FileNotFoundError(f"Gradio output root not found: {output_root}")

    candidates = candidate_image_dirs(output_root)
    if not candidates:
        raise FileNotFoundError(f"No image directories found under Gradio output root: {output_root}")

    return max(
        candidates,
        key=lambda path: max((p.stat().st_mtime for p in path.iterdir() if p.is_file()), default=path.stat().st_mtime),
    )


def image_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return sum(1 for item in path.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_EXTS)


def find_existing_project_images(figures_dir: Path) -> Path | None:
    root = figures_dir / "mineru_images"
    if image_count(root) > 0:
        return root
    if root.exists():
        candidates = [path for path in root.iterdir() if path.is_dir() and image_count(path) > 0]
        if candidates:
            return max(candidates, key=lambda path: max(p.stat().st_mtime for p in path.iterdir() if p.is_file()))
    return None


def infer_pdf_folder_name(images_dir: Path, pdf_path: Path) -> str:
    parts = [part.lower() for part in images_dir.parts]
    if images_dir.parent.name == "mineru_images":
        return images_dir.name
    if images_dir.name.lower() == "images" and images_dir.parent.name.lower() in {"hybrid_auto", "auto"}:
        return images_dir.parent.parent.name
    if "result" in parts and images_dir.name.lower() == "images":
        result_index = parts.index("result")
        if len(images_dir.parts) > result_index + 1:
            return images_dir.parts[result_index + 1]
    if images_dir.name.lower() == "images":
        return images_dir.parent.name
    return pdf_path.stem


def matching_score(images_dir: Path, pdf_path: Path) -> float:
    target = comparable_text(pdf_path.stem)
    if not target:
        return 0.0
    folder_name = comparable_text(infer_pdf_folder_name(images_dir, pdf_path))
    path_text = comparable_text(str(images_dir))
    folder_score = SequenceMatcher(None, target, folder_name).ratio() if folder_name else 0.0
    path_bonus = 0.15 if target[:20] and target[:20] in path_text else 0.0
    return min(1.0, folder_score + path_bonus)


def find_matching_gradio_images(output_root: Path, pdf_path: Path, min_score: float = 0.18) -> Path | None:
    if not output_root.exists():
        return None
    candidates = candidate_image_dirs(output_root)
    if not candidates:
        return None
    scored = []
    for candidate in candidates:
        latest_file_time = max((p.stat().st_mtime for p in candidate.iterdir() if p.is_file()), default=0)
        scored.append((matching_score(candidate, pdf_path), latest_file_time, candidate))
    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    best_score, _, best_path = scored[0]
    if best_score >= min_score:
        return best_path
    return None


def confirm_mineru_start(pdf_path: Path, backend: str, assume_yes: bool) -> None:
    if assume_yes:
        return
    prompt = (
        f"No existing MinerU images were found for:\n"
        f"  {pdf_path}\n\n"
        f"Start MinerU conversion via Docker ({backend}) now? [y/N]: "
    )
    if not sys.stdin.isatty():
        raise RuntimeError("MinerU conversion requires confirmation. Re-run with --yes after user approval.")
    answer = input(prompt).strip().lower()
    if answer not in {"y", "yes"}:
        raise RuntimeError("MinerU conversion cancelled by user.")


def copy_images(images_dir: Path, output_dir: Path, min_size: int, min_dimension: int, prefix: str) -> list[Path]:
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []

    for source in sorted(images_dir.iterdir()):
        if not source.is_file() or source.suffix.lower() not in IMAGE_EXTS:
            continue
        if min_size and source.stat().st_size < min_size:
            continue
        try:
            with Image.open(source) as image:
                width, height = image.size
        except Exception:
            continue
        if min_dimension and (width < min_dimension or height < min_dimension):
            continue

        target = output_dir / f"{prefix}{len(copied) + 1}{source.suffix.lower()}"
        shutil.copy2(source, target)
        copied.append(target)
        print(f"copy image: {source.name} -> {target.name}")

    return copied


def run_mineru_in_docker(
    pdf_path: Path,
    host_output_dir: Path,
    container: str,
    container_workdir: str,
    mineru_command_template: str,
) -> Path:
    run_id = f"{int(time.time())}_{slugify(pdf_path.stem, 40)}"
    container_run_dir = f"{container_workdir.rstrip('/')}/{run_id}"
    container_pdf = f"{container_run_dir}/input/{pdf_path.name}"
    container_output = f"{container_run_dir}/output"

    run_command([
        "docker",
        "exec",
        container,
        "sh",
        "-lc",
        f"rm -rf {shlex.quote(container_run_dir)} && mkdir -p {shlex.quote(container_run_dir + '/input')} {shlex.quote(container_output)}",
    ])

    run_command(["docker", "cp", str(pdf_path), f"{container}:{container_pdf}"])

    command = mineru_command_template.format(
        pdf=shlex.quote(container_pdf),
        out=shlex.quote(container_output),
    )
    run_command(["docker", "exec", container, "sh", "-lc", command])

    host_output_dir.mkdir(parents=True, exist_ok=True)
    run_command(["docker", "cp", f"{container}:{container_output}", str(host_output_dir)])

    copied_output = host_output_dir / "output"
    return copied_output if copied_output.exists() else host_output_dir


def run_mineru_with_docker_run(
    pdf_path: Path,
    host_output_dir: Path,
    docker_image: str,
    docker_gpus: str,
    mineru_command_template: str,
) -> Path:
    host_output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = pdf_path.parent
    container_pdf = f"/data/input/{pdf_path.name}"
    container_output = "/data/output"

    command = mineru_command_template.format(
        pdf=shlex.quote(container_pdf),
        out=shlex.quote(container_output),
    )

    cmd = [
        "docker",
        "run",
        "--rm",
    ]
    if docker_gpus and docker_gpus.lower() not in {"none", "false", "0"}:
        cmd.extend(["--gpus", docker_gpus])
    cmd.extend([
        "-e",
        "MINERU_MODEL_SOURCE=local",
        "-v",
        f"{docker_mount_path(input_dir)}:/data/input:ro",
        "-v",
        f"{docker_mount_path(host_output_dir)}:/data/output",
        docker_image,
        "sh",
        "-lc",
        command,
    ])
    run_command(cmd)
    return host_output_dir


def write_manifest(manifest_path: Path, data: dict) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def run_assisted_crop(
    script_dir: Path,
    pdf_path: Path,
    images_dir: Path,
    crops_dir: Path,
    regions_file: Path,
    debug_dir: Path,
    pages: str,
    match_dpi: int,
    crop_dpi: int,
    min_score: float,
    min_size: int,
    min_dimension: int,
    target_long_edge: int | None,
    min_crop_dpi: int,
    max_crop_dpi: int,
) -> bool:
    cmd = [
        sys.executable,
        str(script_dir / "mineru_assisted_crop.py"),
        str(pdf_path),
        str(images_dir),
        "--out",
        str(crops_dir),
        "--regions",
        str(regions_file),
        "--debug-dir",
        str(debug_dir),
        "--pages",
        pages,
        "--match-dpi",
        str(match_dpi),
        "--crop-dpi",
        str(crop_dpi),
        "--min-score",
        str(min_score),
        "--min-size",
        str(min_size),
        "--min-dimension",
        str(min_dimension),
        "--min-crop-dpi",
        str(min_crop_dpi),
        "--max-crop-dpi",
        str(max_crop_dpi),
    ]
    if target_long_edge:
        cmd.extend(["--target-long-edge", str(target_long_edge)])
    result = run_command(cmd, check=False)
    return result.returncode == 0


def main() -> None:
    default_gradio_root = os.environ.get(
        "MINERU_GRADIO_OUTPUT_ROOT",
        r"E:\software\DockerProject\MinerU\output\gradio",
    )

    parser = argparse.ArgumentParser(description="Run MinerU and extract PDF figures into one output folder")
    parser.add_argument("pdf", type=Path, help="Input PDF")
    parser.add_argument("--mode", choices=["docker-run", "docker", "existing", "latest-gradio"], default="docker-run",
                        help="How to obtain MinerU output")
    parser.add_argument("--out-root", type=Path, default=Path("output"),
                        help="Root output directory; a paper-specific folder is created inside")
    parser.add_argument("--project-name", default=None, help="Override output project folder name")
    parser.add_argument("--docker-image", default=os.environ.get("MINERU_DOCKER_IMAGE", "mineru:latest"),
                        help="Docker image used by --mode docker-run")
    parser.add_argument("--docker-gpus", default=os.environ.get("MINERU_DOCKER_GPUS", "all"),
                        help='GPU value for docker run --gpus. Use "none" to omit --gpus.')
    parser.add_argument("--container", default="mineru-gradio", help="Running Docker container name for --mode docker")
    parser.add_argument("--container-workdir", default="/tmp/pdf-figure-extractor",
                        help="Temporary work directory inside the container")
    parser.add_argument("--mineru-command", default="mineru -p {pdf} -o {out}",
                        help="Command template inside the container. Use {pdf} and {out}.")
    parser.add_argument("--mineru-output", type=Path, default=None,
                        help="Existing MinerU output or images directory for --mode existing")
    parser.add_argument("--mineru-output-root", type=str, default=default_gradio_root,
                        help="Gradio output root or the PDF-specific Gradio output folder for --mode latest-gradio")
    parser.add_argument("--pages", default="all", help='Pages to search, e.g. "all", "2-8", "1,3,5"')
    parser.add_argument("--clarity", choices=sorted(CLARITY_PRESETS), default="4k",
                        help="Output clarity preset. Default: 4k target long edge.")
    parser.add_argument("--target-long-edge", type=int, default=None,
                        help="Override clarity preset with a custom target longest edge in pixels")
    parser.add_argument("--match-dpi", type=int, default=None, help="DPI for locating MinerU images")
    parser.add_argument("--crop-dpi", type=int, default=600,
                        help="Fixed crop DPI used only with --clarity dpi or when no target long edge is set")
    parser.add_argument("--min-crop-dpi", type=int, default=220,
                        help="Minimum crop DPI when using target-long-edge clarity")
    parser.add_argument("--max-crop-dpi", type=int, default=900,
                        help="Maximum crop DPI when using target-long-edge clarity")
    parser.add_argument("--min-score", type=float, default=0.55, help="Minimum template match score")
    parser.add_argument("--min-size", type=int, default=10000, help="Minimum MinerU image file size")
    parser.add_argument("--min-dimension", type=int, default=160, help="Minimum MinerU image width/height")
    parser.add_argument("--copy-only", action="store_true",
                        help="Only copy MinerU images; skip high-DPI PDF-rendered crops")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the interactive confirmation before starting Docker MinerU")
    parser.add_argument("--force-mineru", action="store_true",
                        help="Run Docker MinerU even if existing images are found")
    parser.add_argument("--timestamped", action="store_true",
                        help="Create a timestamped project folder instead of reusing the PDF-name folder")

    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    clarity = CLARITY_PRESETS[args.clarity]
    target_long_edge = args.target_long_edge
    if target_long_edge is None:
        target_long_edge = clarity["target_long_edge"]
    match_dpi = args.match_dpi
    if match_dpi is None:
        match_dpi = clarity["match_dpi"] or 150

    default_project_name = slugify(pdf_path.stem)
    if args.timestamped:
        default_project_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{default_project_name}"
    project_name = args.project_name or default_project_name
    project_dir = args.out_root / project_name
    sources_dir = project_dir / "00_sources"
    mineru_dir = project_dir / "01_mineru"
    figures_dir = project_dir / "02_figures"
    mineru_images_root = figures_dir / "mineru_images"
    mineru_images_dir = mineru_images_root / slugify(pdf_path.stem)
    crops_dir = figures_dir / "crops"
    debug_dir = figures_dir / "debug_matches"
    regions_file = figures_dir / "regions_mineru.json"

    sources_dir.mkdir(parents=True, exist_ok=True)
    copied_pdf = sources_dir / pdf_path.name
    if copied_pdf.resolve() != pdf_path:
        shutil.copy2(pdf_path, copied_pdf)

    existing_project_images = None if args.force_mineru else find_existing_project_images(figures_dir)
    if existing_project_images is not None:
        print(f"Found existing project images, skipping MinerU conversion: {existing_project_images}")
        images_source = existing_project_images
    elif args.mode == "existing":
        if args.mineru_output is None:
            raise ValueError("--mineru-output is required when --mode existing")
        images_source = find_best_images_dir(args.mineru_output)
    elif args.mode == "latest-gradio":
        output_root = normalize_windows_path(args.mineru_output_root)
        if output_root is None:
            raise ValueError("--mineru-output-root is required when --mode latest-gradio")
        images_source = find_matching_gradio_images(output_root, pdf_path) or find_latest_gradio_images(output_root)
    else:
        output_root = normalize_windows_path(args.mineru_output_root)
        existing_gradio_images = None
        if output_root is not None and not args.force_mineru:
            existing_gradio_images = find_matching_gradio_images(output_root, pdf_path)

        if existing_gradio_images is not None:
            print(f"Found existing Gradio MinerU images, skipping MinerU conversion: {existing_gradio_images}")
            images_source = existing_gradio_images
        else:
            if args.mode == "docker-run":
                backend = f"docker run {args.docker_image}"
                confirm_mineru_start(pdf_path, backend, args.yes)
                local_mineru_output = run_mineru_with_docker_run(
                    pdf_path=pdf_path,
                    host_output_dir=mineru_dir,
                    docker_image=args.docker_image,
                    docker_gpus=args.docker_gpus,
                    mineru_command_template=args.mineru_command,
                )
            else:
                backend = f"container {args.container}"
                confirm_mineru_start(pdf_path, backend, args.yes)
                local_mineru_output = run_mineru_in_docker(
                    pdf_path=pdf_path,
                    host_output_dir=mineru_dir,
                    container=args.container,
                    container_workdir=args.container_workdir,
                    mineru_command_template=args.mineru_command,
                )
            images_source = find_best_images_dir(local_mineru_output)

    pdf_folder_name = infer_pdf_folder_name(images_source, pdf_path)
    mineru_images_dir = mineru_images_root / pdf_folder_name

    if images_source.resolve() == mineru_images_dir.resolve():
        copied_images = [p for p in mineru_images_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        print(f"Reuse existing copied images: {mineru_images_dir}")
    else:
        copied_images = copy_images(
            images_source,
            mineru_images_dir,
            min_size=args.min_size,
            min_dimension=args.min_dimension,
            prefix="fig",
        )

    crop_ok = False
    if not args.copy_only:
        crop_ok = run_assisted_crop(
            script_dir=Path(__file__).resolve().parent,
            pdf_path=pdf_path,
            images_dir=mineru_images_dir,
            crops_dir=crops_dir,
            regions_file=regions_file,
            debug_dir=debug_dir,
            pages=args.pages,
            match_dpi=match_dpi,
            crop_dpi=args.crop_dpi,
            min_score=args.min_score,
            min_size=args.min_size,
            min_dimension=args.min_dimension,
            target_long_edge=target_long_edge,
            min_crop_dpi=args.min_crop_dpi,
            max_crop_dpi=args.max_crop_dpi,
        )

    manifest = {
        "pdf": str(pdf_path),
        "project_dir": str(project_dir.resolve()),
        "mode": args.mode,
        "mineru_images_source": str(images_source),
        "mineru_pdf_folder": pdf_folder_name,
        "mineru_images_copied": len(copied_images),
        "mineru_images_dir": str(mineru_images_dir.resolve()),
        "crops_dir": str(crops_dir.resolve()) if crop_ok else None,
        "regions_file": str(regions_file.resolve()) if regions_file.exists() else None,
        "clarity": args.clarity,
        "target_long_edge": target_long_edge,
        "match_dpi": match_dpi,
        "crop_dpi": args.crop_dpi,
        "min_crop_dpi": args.min_crop_dpi,
        "max_crop_dpi": args.max_crop_dpi,
        "crop_ok": crop_ok,
    }
    write_manifest(project_dir / "figure_extraction_manifest.json", manifest)

    print("\nOutput:")
    print(f"  project: {project_dir.resolve()}")
    print(f"  MinerU images: {mineru_images_dir.resolve()}")
    if crop_ok:
        print(f"  high-DPI crops: {crops_dir.resolve()}")
    elif not args.copy_only:
        print("  high-DPI crops: not created; check dependencies or debug output above")


if __name__ == "__main__":
    main()
