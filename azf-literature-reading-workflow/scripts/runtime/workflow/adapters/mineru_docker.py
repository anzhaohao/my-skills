from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz


def docker_status() -> dict:
    docker = shutil.which("docker")
    if not docker:
        return {"available": False, "reason": "docker executable not found"}
    try:
        version = subprocess.run([docker, "--version"], capture_output=True, text=True, check=False)
        ps = subprocess.run([docker, "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=False)
    except OSError as exc:
        return {"available": False, "reason": str(exc)}
    if ps.returncode != 0:
        return {"available": False, "version": version.stdout.strip(), "reason": (ps.stderr or ps.stdout).strip()}
    return {"available": True, "version": version.stdout.strip(), "containers": ps.stdout.splitlines()}


def mineru_image_available(image: str = "mineru:latest") -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    result = subprocess.run([docker, "images", "-q", image], capture_output=True, text=True, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def run_mineru_docker(pdf_path: Path, output_dir: Path, image: str = "mineru:latest") -> subprocess.CompletedProcess:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = hashlib.sha1(str(pdf_path.resolve()).encode("utf-8")).hexdigest()[:12]
    temp_base = Path(os.environ.get("LITERATURE_WORKFLOW_TMP", tempfile.gettempdir())).expanduser().resolve()
    staging_root = temp_base / "azf-literature-workflow" / "docker-staging" / run_id
    input_dir = staging_root / "input"
    staged_output = staging_root / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    staged_output.mkdir(parents=True, exist_ok=True)
    staged_pdf = input_dir / "paper.pdf"
    shutil.copy2(pdf_path, staged_pdf)
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{input_dir.resolve()}:/input",
        "-v",
        f"{staged_output.resolve()}:/output",
        image,
        "mineru",
        "-p",
        "/input/paper.pdf",
        "-o",
        "/output",
        "--backend",
        "pipeline",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if result.returncode == 0:
            shutil.copytree(staged_output, output_dir, dirs_exist_ok=True)
        return result
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def pymupdf_preview_parse(pdf_path: Path, markdown_path: Path, raw_output_path: Path) -> None:
    doc = fitz.open(pdf_path)
    pages = []
    markdown_parts = [
        "# PyMuPDF Preview Parse",
        "",
        "> [!warning] 这不是正式 MinerU 输出",
        "> Docker MinerU 当前不可用。本文件仅用于本地预览、工作区联调和后续人工核对；不得视为通过 MinerU 解析质量门。",
        "",
    ]
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        pages.append({"page": index, "chars": len(text)})
        markdown_parts.append(f"## Page {index}")
        markdown_parts.append("")
        markdown_parts.append(text.strip() or "[no selectable text detected]")
        markdown_parts.append("")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(markdown_parts), encoding="utf-8")
    raw_output_path.write_text(
        json.dumps(
            {
                "parser": "pymupdf_preview",
                "accepted_as_mineru": False,
                "source_pdf": str(pdf_path),
                "pages": pages,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )